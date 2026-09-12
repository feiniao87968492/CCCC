import re
import os

sec = "paper/sections"
for fn in sorted(os.listdir(sec)):
    if not fn.endswith(".tex"):
        continue
    skip = bool(re.search(r"appendix|A_code", fn, re.I))
    content = open(os.path.join(sec, fn), encoding="utf-8").read()
    for env in ["tabular", "longtable", "tabular*"]:
        pattern = r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{" + re.escape(env) + r"\}"
        for i, match in enumerate(re.finditer(pattern, content, re.DOTALL), 1):
            table_text = match.group()
            row_count = table_text.count("\\\\")
            flag = " SKIP" if skip else ""
            print(f"{fn} {env}#{i}: rows={row_count}{flag}")
