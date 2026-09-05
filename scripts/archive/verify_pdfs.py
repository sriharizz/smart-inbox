import os

pdf_base = r"c:\projects\SmartInbox\test-data\pdfs"
categories = [
    ("digital_forms", "2. Normal digital PDFs (e.g. CIOMS/MedWatch forms) - Req: >= 5"),
    ("scanned_handwritten", "3. Scanned/handwritten-style PDFs - Req: >= 2"),
    ("literature_articles", "4. Medical literature articles - Req: >= 5"),
    ("non_english", "5. Non-English language PDFs - Req: >= 2"),
    ("quality_complaints", "6a. Quality-complaint-only PDFs - Req: >= 2"),
    ("medical_info", "6b. Info-request-only PDFs - Req: >= 2"),
    ("irrelevant", "7. Irrelevant / marketing PDFs - Req: >= 1"),
]

print("=" * 65)
print("SECTION 6 PDF INVENTORY CHECK")
print("=" * 65)
total_pdfs = 0
for folder, desc in categories:
    fpath = os.path.join(pdf_base, folder)
    if os.path.exists(fpath):
        files = [f for f in os.listdir(fpath) if f.endswith(".pdf")]
    else:
        files = []
    total_pdfs += len(files)
    print(f"\n[DIR] {folder.upper()} (Current count: {len(files)})")
    print(f"   Target: {desc}")
    for f in files:
        print(f"    - {f}")

print("\n" + "=" * 65)
print(f"Total PDFs currently generated: {total_pdfs} / 19")
print("=" * 65)
