import re
import json
import logging
from typing import Any, Dict, Optional, Tuple, List

logger = logging.getLogger("smartinbox.json_repair")


def extract_json_candidate(text: str) -> str:
    """
    Extracts the most likely candidate JSON string from raw LLM output.
    Removes markdown code fences, leading/trailing prose, and whitespace.
    """
    if not text:
        return ""

    cleaned = text.strip()

    # 1. Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = r"^```(?:json|JSON)?\s*\n?(.*?)\n?```$"
    fence_match = re.search(fence_pattern, cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        # If code fence is opened but maybe not cleanly closed or has lead-in
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                p = part.strip()
                if p.lower().startswith("json"):
                    p = p[4:].strip()
                if (p.startswith("{") and p.endswith("}")) or (p.startswith("[") and p.endswith("]")):
                    cleaned = p
                    break

    # 2. Extract substring from first '{' to last '}' if surrounding text exists
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]

    return cleaned.strip()


def fix_unescaped_control_chars(text: str) -> str:
    """
    Replaces unescaped raw newlines, carriage returns, and tabs inside JSON string literals
    with their escaped equivalents (\\n, \\r, \\t).
    """
    result = []
    in_string = False
    escape = False

    for char in text:
        if escape:
            result.append(char)
            escape = False
            continue

        if char == "\\":
            escape = True
            result.append(char)
            continue

        if char == '"':
            in_string = not in_string
            result.append(char)
            continue

        if in_string:
            if char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(char)
        else:
            result.append(char)

    return "".join(result)


def close_truncated_json(text: str) -> str:
    """
    If a JSON string was truncated mid-generation, closes open strings,
    dangling colons/keys, and all open brackets and braces in correct reverse stack order.
    """
    in_string = False
    escape = False
    stack: List[str] = []

    for char in text:
        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char in ("{", "["):
                stack.append(char)
            elif char == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif char == "]":
                if stack and stack[-1] == "[":
                    stack.pop()

    repaired = text.rstrip()

    # If string was left open, close it
    if in_string:
        repaired += '"'

    # Remove any trailing comma or dangling colon
    repaired = re.sub(r",\s*$", "", repaired)
    if repaired.endswith(":"):
        repaired += ' "Not stated"'

    # Pop remaining open structures
    while stack:
        opening = stack.pop()
        if opening == "{":
            repaired += "}"
        elif opening == "[":
            repaired += "]"

    return repaired


def repair_json_string(raw_json: str) -> str:
    """
    Applies multi-pass deterministic heuristic repairs to malformed JSON.
    """
    if not raw_json:
        return "{}"

    candidate = extract_json_candidate(raw_json)

    # Pass 1: Smart quotes normalization
    candidate = candidate.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # Pass 2: Clean unescaped control characters inside string literals
    candidate = fix_unescaped_control_chars(candidate)

    # Pass 3: Remove trailing commas before } or ]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    # Pass 4: Fix unquoted property keys (e.g. { patient: -> { "patient": )
    candidate = re.sub(r'(?<=[{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', candidate)

    # Pass 5: Fix missing comma between consecutive key-value pairs (e.g. "val" \n "key":)
    candidate = re.sub(r'("(?:[^"\\]|\\.)*")\s*\n\s*("(?:\w+)"\s*:)', r'\1,\n\2', candidate)
    candidate = re.sub(r'(true|false|null|\d+)\s*\n\s*("(?:\w+)"\s*:)', r'\1,\n\2', candidate)
    candidate = re.sub(r'([}\]])\s*\n\s*("(?:\w+)"\s*:)', r'\1,\n\2', candidate)

    # Pass 6: Check truncation and close structures if needed
    candidate = close_truncated_json(candidate)

    # Pass 7: Re-clean trailing commas that might have been revealed after closing
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    return candidate


def robust_json_loads(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Extracts, parses, and repairs JSON from raw LLM output.
    Returns:
        (parsed_dict, error_message)
        If successful: (dict, None)
        If failed: (None, error_str)
    """
    if not text or not text.strip():
        return None, "Empty LLM response text"

    # Attempt 1: Direct extraction and parse
    candidate = extract_json_candidate(text)
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data, None
        return None, f"Expected JSON object, got {type(data).__name__}"
    except json.JSONDecodeError as e1:
        first_error = str(e1)
        logger.debug(f"Direct JSON parse failed ({first_error}). Attempting repair.")

    # Attempt 2: Standard deterministic repair
    try:
        repaired = repair_json_string(candidate)
        data = json.loads(repaired)
        if isinstance(data, dict):
            logger.info("Successfully parsed LLM JSON using deterministic repair.")
            return data, None
        return None, f"Repaired JSON resulted in {type(data).__name__}, expected object"
    except json.JSONDecodeError as e2:
        logger.debug(f"First-pass repair failed ({e2}). Attempting aggressive repair.")

    # Attempt 3: Aggressive fallback repair (single quotes to double quotes)
    try:
        sq_candidate = re.sub(r"'([a-zA-Z0-9_]+)'\s*:", r'"\1":', candidate)
        sq_candidate = re.sub(r":\s*'([^']*)'", r': "\1"', sq_candidate)
        repaired_sq = repair_json_string(sq_candidate)
        data = json.loads(repaired_sq)
        if isinstance(data, dict):
            logger.info("Successfully parsed LLM JSON using aggressive quote repair.")
            return data, None
    except Exception:
        pass

    return None, f"JSONDecodeError: {first_error}"


def validate_extraction_schema(
    raw_data: Any,
    is_icsr: bool,
    is_pqc: bool,
    is_mi: bool,
    is_not_relevant: bool,
    document_text: str = ""
) -> Tuple[bool, str]:
    """
    Validates that parsed raw_data conforms to the required multi-category extraction schema,
    preserves all active categories, and does not silently accept an empty 'Not stated' hull
    when the source document contains substantial clinical text.
    
    Returns:
        (is_valid, reason)
    """
    if not isinstance(raw_data, dict):
        return False, f"Expected JSON object root, got {type(raw_data).__name__}"

    # 1. Multi-label & category presence validation
    if is_icsr:
        icsr_dict = raw_data.get("icsr")
        if not isinstance(icsr_dict, dict):
            return False, "Missing or invalid 'icsr' object for active ICSR category"
        if not any(k in icsr_dict for k in ("patient", "product", "reaction", "reporter")):
            return False, "'icsr' object is missing essential sections (patient, product, reaction, reporter)"

    if is_pqc:
        pqc_dict = raw_data.get("pqc")
        if not isinstance(pqc_dict, dict):
            return False, "Missing or invalid 'pqc' object for active PQC category"
        if not any(k in pqc_dict for k in ("product_name", "lot_number", "defect_type", "defect_description")):
            return False, "'pqc' object is missing essential fields (product_name, lot_number, defect_type)"

    if is_mi:
        mi_dict = raw_data.get("mi")
        if not isinstance(mi_dict, dict):
            return False, "Missing or invalid 'mi' object for active MI category"
        if not any(k in mi_dict for k in ("product_or_topic", "inquiry_type", "question_text")):
            return False, "'mi' object is missing essential fields (product_or_topic, question_text)"

    if is_not_relevant:
        nr_dict = raw_data.get("not_relevant")
        if not isinstance(nr_dict, dict):
            return False, "Missing or invalid 'not_relevant' object for active Not Relevant category"

    # 2. Suspicious Empty Hull Check (Requirement 6)
    # If the document contains substantial text (>300 chars) with clinical/product indicators,
    # but the extracted payload has ZERO confirmed/populated fields (all fields are "Not stated" or empty),
    # this indicates an extraction hallucination / empty hull that should not be silently accepted.
    doc_len = len(document_text.strip()) if document_text else 0
    if doc_len > 300 and not is_not_relevant:
        clinical_keywords = [
            "patient", "adverse", "reaction", "hospital", "mg", "dose", "tablet", 
            "vial", "batch", "lot", "defect", "complaint", "inquiry", "sepsis", 
            "anaphylaxis", "seizure", "angioedema", "rash", "fever", "pain", "doctor", "dr."
        ]
        doc_lower = document_text.lower()
        has_clinical_content = sum(1 for kw in clinical_keywords if kw in doc_lower) >= 2

        if has_clinical_content:
            extracted_values = []
            if is_icsr and isinstance(raw_data.get("icsr"), dict):
                icsr_obj = raw_data["icsr"]
                for sec_key in ("patient", "reporter", "product", "reaction"):
                    sec = icsr_obj.get(sec_key)
                    if isinstance(sec, dict):
                        for k, v in sec.items():
                            if k not in ("status", "citation", "seriousness_criteria") and isinstance(v, str):
                                extracted_values.append(v.strip().lower())
                            elif k == "seriousness_criteria" and isinstance(v, list):
                                extracted_values.extend([str(item).strip().lower() for item in v])
            if is_pqc and isinstance(raw_data.get("pqc"), dict):
                pqc_obj = raw_data["pqc"]
                for k, v in pqc_obj.items():
                    if k not in ("citation", "packaging_breached", "photo_detected", "requires_human_review") and isinstance(v, str):
                        extracted_values.append(v.strip().lower())
            if is_mi and isinstance(raw_data.get("mi"), dict):
                mi_obj = raw_data["mi"]
                for k, v in mi_obj.items():
                    if k not in ("citation", "explicit_no_ae_no_pqc") and isinstance(v, str):
                        extracted_values.append(v.strip().lower())

            # Count fields that are populated with substantive information (not "not stated", "none", "unknown", "")
            substantive_count = sum(
                1 for val in extracted_values 
                if val and val not in ("not stated", "none", "unknown", "n/a", "-")
            )

            if substantive_count == 0 and len(extracted_values) > 0:
                return False, (
                    f"Suspicious empty extraction hull: document contains {doc_len} characters "
                    f"with strong clinical signals, but all {len(extracted_values)} extracted fields are 'Not stated'."
                )

    return True, "Valid"

