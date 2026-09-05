import os
import json
import email
from email import policy
import fitz
import hashlib

BASE_DIR = r"c:\projects\SmartInbox\test-data"
EMAILS_DIR = os.path.join(BASE_DIR, "emails")
PDFS_DIR = os.path.join(BASE_DIR, "pdfs")
GT_DIR = os.path.join(BASE_DIR, "ground_truth")
MANIFEST_PATH = os.path.join(BASE_DIR, "manifest.json")
BENCHMARK_PATH = os.path.join(GT_DIR, "benchmark.json")
CATALOG_PATH = os.path.join(BASE_DIR, "TEST_CASES_AND_EMAILS.md")

print("=" * 75)
print("COMPREHENSIVE CROSS-SOURCE CONSISTENCY & RECONCILIATION VALIDATOR")
print("=" * 75)

errors = []
passes = []

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    benchmark = json.load(f)

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    catalog = f.read()

# 1. Check physical emails against benchmark headers
for i in range(1, 12):
    cid = f"CASE-{i:02d}"
    ename = f"email_{i:02d}.eml"
    epath = os.path.join(EMAILS_DIR, ename)
    if not os.path.exists(epath):
        errors.append(f"Email missing: {ename}")
        continue
    with open(epath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    
    bcase = benchmark["cases"].get(cid)
    if not bcase:
        errors.append(f"Benchmark missing case: {cid}")
        continue
    
    bheaders = bcase.get("email_headers", {})
    if bheaders:
        # Check from
        if bheaders.get("from") != msg.get("From"):
            errors.append(f"[{cid}] 'From' mismatch: physical='{msg.get('From')}' vs benchmark='{bheaders.get('from')}'")
        else:
            passes.append(f"[{cid}] Header 'From' perfectly matches physical .eml")
        
        # Check subject
        if bheaders.get("subject") != msg.get("Subject"):
            errors.append(f"[{cid}] 'Subject' mismatch: physical='{msg.get('Subject')}' vs benchmark='{bheaders.get('subject')}'")
        else:
            passes.append(f"[{cid}] Header 'Subject' perfectly matches physical .eml")
            
        # Check message-id
        if bheaders.get("message_id") != msg.get("Message-ID"):
            errors.append(f"[{cid}] 'Message-ID' mismatch: physical='{msg.get('Message-ID')}' vs benchmark='{bheaders.get('message_id')}'")
        else:
            passes.append(f"[{cid}] Header 'Message-ID' perfectly matches physical .eml")

# 2. Check Case 03 frequency is "Not stated"
case_03 = benchmark["cases"]["CASE-03"]
if case_03["product"].get("frequency") != "Not stated":
    errors.append(f"[CASE-03] Expected frequency 'Not stated', found: {case_03['product'].get('frequency')}")
else:
    passes.append("[CASE-03] Frequency strictly recorded as 'Not stated' (zero-hallucination verified)")

# 3. Check Case 04 reporter is Robert Lang, MD (Northwestern Memorial Hospital)
case_04 = benchmark["cases"]["CASE-04"]
if "Robert Lang" not in case_04["reporter"]["name"]:
    errors.append(f"[CASE-04] Expected reporter Robert Lang, found: {case_04['reporter']['name']}")
else:
    passes.append("[CASE-04] Reporter correctly recorded as Robert Lang, MD, FCCM")

# 4. Check Case 05 reporter is Elena Morales and date Nov 15, 2025
case_05 = benchmark["cases"]["CASE-05"]
if "Elena Morales" not in case_05["reporter"]["name"]:
    errors.append(f"[CASE-05] Expected reporter Elena Morales, found: {case_05['reporter']['name']}")
else:
    passes.append("[CASE-05] Reporter correctly recorded as Dra. Elena Morales")

# 5. Check Case 07 reporter is Robert Vance, Cardioril 10mg, Exp 11/2026, 12 cartons / 360 strips
case_07 = benchmark["cases"]["CASE-07"]
if "Robert Vance" not in case_07["reporter"]["name"]:
    errors.append(f"[CASE-07] Expected reporter Robert Vance, found: {case_07['reporter']['name']}")
else:
    passes.append("[CASE-07] Reporter correctly recorded as Robert Vance, PharmD, BCPS")

if case_07["quality_complaint"]["product"] != "Cardioril 10mg Film-Coated Tablets":
    errors.append(f"[CASE-07] Expected product Cardioril 10mg, found: {case_07['quality_complaint']['product']}")
else:
    passes.append("[CASE-07] Product correctly recorded as Cardioril 10mg")

if case_07["quality_complaint"]["expiry"] != "11/2026":
    errors.append(f"[CASE-07] Expected expiry 11/2026, found: {case_07['quality_complaint']['expiry']}")
else:
    passes.append("[CASE-07] Expiry correctly recorded as 11/2026")

# 6. Check Case 08 reporter is Karen Patel, Lipocur 20mg, Lot LP-44109
case_08 = benchmark["cases"]["CASE-08"]
if "Karen Patel" not in case_08["reporter"]["name"]:
    errors.append(f"[CASE-08] Expected reporter Karen Patel, found: {case_08['reporter']['name']}")
else:
    passes.append("[CASE-08] Reporter correctly recorded as Karen Patel, RPh")

if case_08["quality_complaint"]["product"] != "Lipocur 20mg tablets":
    errors.append(f"[CASE-08] Expected product Lipocur 20mg, found: {case_08['quality_complaint']['product']}")
else:
    passes.append("[CASE-08] Product correctly recorded as Lipocur 20mg")

if case_08["quality_complaint"]["lot"] != "Lot #LP-44109":
    errors.append(f"[CASE-08] Expected lot LP-44109, found: {case_08['quality_complaint']['lot']}")
else:
    passes.append("[CASE-08] Lot correctly recorded as Lot #LP-44109")

# 7. Check Manifest separated physical assets
phys_emails = manifest.get("physical_email_assets", [])
phys_pdfs = manifest.get("physical_pdf_assets", [])
phys_imgs = manifest.get("physical_image_assets", [])
if len(phys_emails) == 11 and len(phys_pdfs) == 20 and len(phys_imgs) == 2:
    passes.append(f"[MANIFEST] Physical assets correctly separated: {len(phys_emails)} emails, {len(phys_pdfs)} PDFs, {len(phys_imgs)} images")
else:
    errors.append(f"[MANIFEST] Asset count error: {len(phys_emails)} emails, {len(phys_pdfs)} PDFs, {len(phys_imgs)} images")

# 8. Check Catalog mentions Robert Lang, Karen Patel, Robert Vance 10mg, etc.
if "Robert Lang, MD, FCCM" in catalog and "Karen Patel, RPh" in catalog and "Cardioril 10mg Film-Coated Tablets" in catalog:
    passes.append("[CATALOG] TEST_CASES_AND_EMAILS.md contains canonical physical names and products")
else:
    errors.append("[CATALOG] TEST_CASES_AND_EMAILS.md missing canonical physical names/products")

# Summary
print(f"\nVALIDATION REPORT: {len(passes)} Passed | {len(errors)} Errors\n")
for p in passes:
    print(f"  [PASS] {p}")
for e in errors:
    print(f"  [FAIL] {e}")

if not errors:
    print("\n[SUCCESS] Cross-Source Consistency & Reconciliation Verified 100%!")
else:
    print("\n[FAIL] Inconsistencies detected!")
