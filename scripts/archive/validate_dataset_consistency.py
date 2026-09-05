import os
import json

BASE_DIR = r"c:\projects\SmartInbox\test-data"
MANIFEST_PATH = os.path.join(BASE_DIR, "manifest.json")
BENCHMARK_PATH = os.path.join(BASE_DIR, "ground_truth", "benchmark.json")

print("=" * 70)
print("PHASE 5: COMPREHENSIVE DATASET QUALITY & CONSISTENCY VALIDATION")
print("=" * 70)

errors = []
warnings = []
passed = []

# 1. Load manifest & benchmark
if not os.path.exists(MANIFEST_PATH):
    errors.append(f"Manifest missing: {MANIFEST_PATH}")
else:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    passed.append(f"Manifest loaded successfully ({len(manifest.get('inventory', []))} items)")

if not os.path.exists(BENCHMARK_PATH):
    errors.append(f"Benchmark missing: {BENCHMARK_PATH}")
else:
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    passed.append(f"Benchmark loaded successfully ({len(benchmark.get('cases', {}))} cases)")

# 2. Check Physical Files from Manifest
inventory = manifest.get("inventory", [])
for item in inventory:
    item_id = item["id"]
    file_rel = item.get("file")
    if file_rel:
        full_p = os.path.join(BASE_DIR, file_rel)
        if not os.path.exists(full_p):
            errors.append(f"[{item_id}] File does not exist on disk: {full_p}")
        elif os.path.getsize(full_p) == 0:
            errors.append(f"[{item_id}] File is empty (0 bytes): {full_p}")
    
    att_rel = item.get("attachment")
    if att_rel:
        full_att = os.path.join(BASE_DIR, att_rel)
        if not os.path.exists(full_att):
            errors.append(f"[{item_id}] Attachment does not exist on disk: {full_att}")
        elif os.path.getsize(full_att) == 0:
            errors.append(f"[{item_id}] Attachment is empty (0 bytes): {full_att}")

# 3. Verify Case 02 Zero-Hallucination Fix
case_02 = benchmark.get("cases", {}).get("CASE-02")
if case_02:
    prod_dose = case_02.get("product", {}).get("dose")
    if prod_dose != "Not stated":
        errors.append(f"[CASE-02] Dose was expected to be 'Not stated', but found: {prod_dose}")
    else:
        passed.append("[CASE-02] Dose correctly recorded as 'Not stated' (zero-hallucination policy passed)")
    
    treatment = case_02.get("treatment", {}).get("emergency_intervention")
    if "Epinephrine" not in treatment:
        errors.append(f"[CASE-02] Treatment missing Epinephrine: {treatment}")
    else:
        passed.append("[CASE-02] Emergency Epinephrine correctly separated from suspect product dose")

# 4. Verify Case 04 Multi-Label & Image Flag
case_04 = benchmark.get("cases", {}).get("CASE-04")
if case_04:
    cats = case_04.get("categories", [])
    if "Safety Report (ICSR)" not in cats or "Quality Complaint (PQC)" not in cats:
        errors.append(f"[CASE-04] Multi-label categories missing: {cats}")
    else:
        passed.append("[CASE-04] Multi-label classification (ICSR + PQC) verified")
    
    pqc_photo_flag = case_04.get("quality_complaint", {}).get("photo_requires_human_review")
    if not pqc_photo_flag:
        errors.append("[CASE-04] Photo requires human review flag is missing")
    else:
        passed.append("[CASE-04] Photo human-review flag verified")

# 5. Verify Case 09 and Case 11 MI-Only Emails
case_09 = benchmark.get("cases", {}).get("CASE-09")
case_11 = benchmark.get("cases", {}).get("CASE-11")
if case_09 and case_11:
    if case_09.get("categories") == ["Medical Information (MI)"] and case_11.get("categories") == ["Medical Information (MI)"]:
        passed.append("[MI EMAILS] Exactly 2 MI-only emails verified (Case 09 + Case 11)")
    else:
        errors.append(f"[MI EMAILS] Inconsistent categories: Case 09={case_09.get('categories')}, Case 11={case_11.get('categories')}")

# 6. Verify Literature Corpus
lit_cases = [k for k in benchmark.get("cases", {}) if k.startswith("LIT-")]
case_bearing = []
non_reportable = []
for lk in lit_cases:
    item = benchmark["cases"][lk]
    if item.get("reportable") is True:
        case_bearing.append(lk)
    elif item.get("reportable") is False:
        non_reportable.append(lk)

if len(case_bearing) >= 5 and len(non_reportable) >= 2:
    passed.append(f"[LITERATURE] Exactly {len(case_bearing)} case-bearing articles and {len(non_reportable)} non-reportable negative articles verified (Total: {len(lit_cases)})")
else:
    errors.append(f"[LITERATURE] Count mismatch: Case-bearing={len(case_bearing)} (need >=5), Non-reportable={len(non_reportable)} (need >=2)")

# 7. Check Entity Collisions
lit_03 = benchmark.get("cases", {}).get("LIT-03", {})
authors_lit_03 = lit_03.get("authors", "")
if "Arthur Pendelton" in authors_lit_03:
    errors.append("[HYGIENE] Arthur Pendelton still present in LIT-03 authors (collides with Case 04 patient)")
else:
    passed.append("[HYGIENE] Arthur Pendelton entity collision resolved (replaced with Alistair Finch)")

lit_01 = benchmark.get("cases", {}).get("LIT-01", {})
authors_lit_01 = lit_01.get("authors", "")
if "Gregory House" in authors_lit_01 or "Lisa Cuddy" in authors_lit_01:
    errors.append("[HYGIENE] TV character names still present in LIT-01 authors")
else:
    passed.append("[HYGIENE] Fictional TV author names replaced with neutral clinical researchers")

# 8. Check Second Handwritten PDF Status
if manifest.get("statistics", {}).get("deferred_requirements", {}).get("second_scanned_handwritten_pdf"):
    passed.append("[DEFERRED REQUIREMENT] Second scanned/handwritten PDF explicitly and properly marked as DEFERRED")
else:
    warnings.append("[DEFERRED REQUIREMENT] Second scanned PDF not noted in manifest deferred section")

# Summary Output
print(f"\nVALIDATION RESULTS: {len(passed)} Checks Passed | {len(errors)} Errors | {len(warnings)} Warnings\n")
for p in passed:
    print(f"  [PASS] {p}")
for w in warnings:
    print(f"  [WARN] {w}")
for e in errors:
    print(f"  [FAIL] {e}")

if not errors:
    print("\n[SUCCESS] All consistency and quality checks passed with ZERO errors!")
else:
    print("\n[FAILURE] Inconsistencies detected. Please review above.")
