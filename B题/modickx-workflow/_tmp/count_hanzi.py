# -*- coding: utf-8 -*-
import os, re, glob

root = os.path.join(os.path.dirname(__file__), "..", "paper", "sections")
root = os.path.abspath(root)
files = sorted(glob.glob(os.path.join(root, "*.tex")))

def hanzi(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))

body = 0
print("file hanzi")
for f in files:
    t = open(f, encoding="utf-8").read()
    n = hanzi(t)
    body += n
    print(f"{os.path.basename(f):20s} {n}")
print("BODY", body, "pages~", round(body / 900, 2))

main = os.path.join(root, "..", "main.tex")
mt = open(main, encoding="utf-8").read()
m = re.search(r"\\begin\{abstract\}(.*)\\end\{abstract\}", mt, re.S)
print("ABSTRACT", hanzi(m.group(1) if m else ""))

print("\n--- captions ---")
for f in files + [main]:
    s = open(f, encoding="utf-8").read()
    i = 0
    while True:
        m = re.search(r"\\caption\*?\s*(\[[^\]]*\]\s*)?\{", s[i:])
        if not m:
            break
        start = i + m.end(); depth = 1; j = start
        while j < len(s) and depth:
            if s[j] == "{": depth += 1
            elif s[j] == "}": depth -= 1
            j += 1
        inner = s[start:j-1]; i = j
        t = re.sub(r"\\(label|ref|cite|footnote)\{[^}]*\}", "", inner)
        t = re.sub(r"\$[^$]*\$", "", t)
        t = re.sub(r"\\[a-zA-Z]+\*?", "", t)
        cn = re.findall(r"[\u4e00-\u9fff]", t)
        mark = "OK" if len(cn) <= 20 else "LONG"
        print(f"  {mark} {os.path.basename(f):20s} {len(cn):2d} {''.join(cn)}")

print("\n--- stacking (3 text lines between floats) ---")
for f in files:
    lines = open(f, encoding="utf-8").read().splitlines()
    a = 0; t = 0; c = 0
    e = 0; ta = 0; ca = 0
    for line in lines:
        if re.search(r"\\end\{(figure|table)\}", line):
            a = 1; t = 0
            e = 1; ta = 0
            continue
        if a and re.search(r"\\begin\{(figure|table)\}", line):
            if t < 3:
                c += 1
            a = 0
        if a and re.search(r"[a-zA-Z\u4e00-\u9fff]{3,}", line):
            t += 1
        if a and t >= 3:
            a = 0
        if e and re.search(r"[a-zA-Z\u4e00-\u9fff]{10,}", line):
            ta += 1
        if e and ta >= 3:
            e = 0
        if e and re.search(r"\\(section|subsection|chapter|begin\{figure|begin\{table)", line):
            if ta < 3:
                ca += 1
            e = 0
    if e and ta < 3:
        ca += 1
    print(f"  {os.path.basename(f):20s} stack={c} missing_analysis={ca}")
