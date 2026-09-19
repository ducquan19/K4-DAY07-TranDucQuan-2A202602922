import csv
import re
from pathlib import Path

D = Path("data/hoc-phi")
REQ = ["doc_id", "title", "source_url", "retrieved_at", "document_version", "audience"]
mds = sorted(D.glob("*.md"))
rows = list(csv.DictReader(open(D / "sources.csv", encoding="utf-8")))
ids, auds = [], {}

print("=== KIEM TRA METADATA TUNG FILE ===")
for p in mds:
    content = p.read_text(encoding="utf-8")
    parts = content.split("---")
    if len(parts) < 3:
        print(f"{p.name:45} THIEU FRONTMATTER")
        continue
    fm = dict(re.findall(r"^(\w+):\s*(.+)$", parts[1], re.M))
    doc_id = fm.get("doc_id", "").strip().strip('"').strip("'")
    aud = fm.get("audience", "").strip().strip('"').strip("'")
    ids.append(doc_id)
    auds[aud] = auds.get(aud, 0) + 1
    
    missing = [k for k in REQ if k not in fm]
    status = "OK" if (not missing and doc_id == p.stem) else f"THIEU METADATA: {missing}"
    print(f"{p.name:45} {status}")

print("\n=== TONG HOP CHECKPOINT 2 ===")
print("so file :", len(mds), "(can 5-10)")
csv_match = "khop" if sorted(r["doc_id"] for r in rows) == sorted(ids) else "LECH"
print("csv     :", csv_match)
print("audience:", auds)

if len(mds) >= 5 and csv_match == "khop" and len(auds) >= 2:
    print("\n>>> DAT TAT CA DIEU KIEN CHECKPOINT 2! <<<")
else:
    print("\n>>> CHUA DAT CHECKPOINT 2 <<<")
