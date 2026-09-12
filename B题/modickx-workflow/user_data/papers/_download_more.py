#!/usr/bin/env python3
"""Download remaining OA PDFs and retry Sci-Hub mirrors with a browser UA."""
from __future__ import annotations

import os
import ssl
import time
import urllib.error
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()


def is_pdf(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def fetch(url: str, dest: str, timeout: int = 60) -> tuple[bool, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/pdf,application/octet-stream,*/*",
            "Referer": url,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            data = resp.read()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    if not data.startswith(b"%PDF"):
        head = data[:80].decode("latin-1", "replace").replace("\n", " ")
        return False, f"not_pdf ({len(data)} bytes) {head}"
    with open(dest, "wb") as f:
        f.write(data)
    return True, f"ok {len(data)} bytes"


def try_urls(name: str, urls: list[str]) -> None:
    dest = os.path.join(OUT, name)
    if is_pdf(dest):
        print(f"SKIP exists\t{name}")
        return
    for url in urls:
        print(f"TRY\t{name}\t{url}")
        ok, msg = fetch(url, dest)
        print(f"  -> {msg}")
        if ok:
            return
        time.sleep(1.0)
    print(f"FAIL\t{name}")


def scihub_urls(doi: str) -> list[str]:
    doi = doi.strip().lstrip("/")
    hosts = [
        "sci-hub.se",
        "sci-hub.st",
        "sci-hub.ru",
        "sci-hub.su",
        "sci-hub.red",
        "sci-hub.box",
        "sci-hub.al",
        "sci-hub.ee",
        "sci-hub.mk",
    ]
    urls = []
    for h in hosts:
        urls.append(f"https://{h}/{doi}")
        urls.append(f"https://{h}/{doi}.pdf")
    urls.append(f"https://sci.bban.top/pdf/{doi}.pdf")
    urls.append(f"https://sci.bban.top/pdf/{doi.lower()}.pdf")
    return urls


def extract_pdf_from_html(url: str, dest: str) -> tuple[bool, str]:
    """Sci-Hub landing pages embed an iframe / embed pointing at the PDF."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=45, context=CTX) as resp:
            html = resp.read().decode("utf-8", "replace")
            final = resp.geturl()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    import re

    cands = []
    for m in re.finditer(r'(?:iframe|embed)[^>]+src=["\']([^"\']+)["\']', html, re.I):
        cands.append(m.group(1))
    for m in re.finditer(r'(?:href|src)=["\']([^"\']+\.pdf[^"\']*)["\']', html, re.I):
        cands.append(m.group(1))
    for m in re.finditer(r'location\.href\s*=\s*["\']([^"\']+)["\']', html, re.I):
        cands.append(m.group(1))
    if not cands:
        return False, f"no pdf link in html ({len(html)} bytes) {final}"
    from urllib.parse import urljoin

    for c in cands:
        pdf_url = urljoin(final, c.replace("\\/", "/"))
        print(f"  html-> {pdf_url}")
        ok, msg = fetch(pdf_url, dest, timeout=90)
        if ok:
            return True, msg
        print(f"    {msg}")
    return False, "html candidates failed"


# --- OA / known public URLs ---
jobs = [
    (
        "Galceran2013_Survey_Coverage_Path_Planning.pdf",
        [
            "https://dugi-doc.udg.edu/bitstream/handle/10256/9088/Survey-coverage-path-planning.pdf?sequence=1",
            "https://scispace.com/pdf/a-survey-on-coverage-path-planning-for-robotics-584p6o3a2k.pdf",
        ],
    ),
    (
        "Dogancay2022_Optimal_Geometries_AOA_Bayesian.pdf",
        [
            "https://www.mdpi.com/1424-8220/22/24/9802/pdf",
            "https://www.mdpi.com/1424-8220/22/24/9802/pdf?version=1670855695",
            "https://mdpi-res.com/d_attachment/sensors/sensors-22-09802/article_deploy/sensors-22-09802-v2.pdf?version=1670855695",
            "https://mdpi-res.com/d_attachment/sensors/sensors-22-09802/article_deploy/sensors-22-09802.pdf",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9785418/pdf/sensors-22-09802.pdf",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC9785418/pdf/sensors-22-09802.pdf",
            "https://europepmc.org/articles/pmc9785418?pdf=render",
        ],
    ),
    (
        "Magers2016_UAV_RF_Emitter_Geolocation_AFIT.pdf",
        [
            "https://scholar.afit.edu/cgi/viewcontent.cgi?article=1437&context=etd",
            "https://apps.dtic.mil/sti/pdfs/AD1012071.pdf",
            "https://apps.dtic.mil/sti/tr/pdf/AD1012071.pdf",
            "https://apps.dtic.mil/dtic/tr/fulltext/u2/1012071.pdf",
        ],
    ),
    (
        "Jung1901_Kleinste_Kugel_Crelle.pdf",
        [
            "https://www.degruyterbrill.com/document/doi/10.1515/crll.1901.123.241/pdf",
            "https://www.degruyter.com/document/doi/10.1515/crll.1901.123.241/pdf",
        ],
    ),
    (
        "Bishop2009_ISSNIP_Sensor_Target_Geometries_RSS.pdf",
        [
            "https://www.csc.kth.se/~patric/publications/BishopJensfeltISSNIP09.pdf",
        ],
    ),
    (
        "Wikipedia_Jungs_theorem.pdf",
        [],
    ),
]

for name, urls in jobs:
    if urls:
        try_urls(name, urls)

# --- Sci-Hub for remaining paywalled DOIs (correct ones) ---
scihub_jobs = [
    ("Stansfield1947_Statistical_theory_of_DF_fixing.pdf", "10.1049/ji-3a-2.1947.0096"),
    ("Dogancay2005_Bearings_Only_TLS.pdf", "10.1016/j.sigpro.2005.03.007"),
    ("Bishop2010_Optimality_analysis_sensor_target_geometries.pdf", "10.1016/j.automatica.2009.12.003"),
    ("Xu2017_Optimal_Sensor_Placement_3D_AOA.pdf", "10.1109/TAES.2017.2667999"),
    ("Dogancay2012_UAV_Path_Planning_Passive_Emitter.pdf", "10.1109/TAES.2012.6178054"),
    ("Gholami2015_Worst_Case_Position_Error_Bearing_Only.pdf", "10.1109/WPNC.2015.7413217"),
    ("Ruan2025_UAV_Directional_Emitter_Joint_Estimation.pdf", "10.1109/LWC.2024.3519640"),
    ("Ruan2023_Multi_Stage_RF_Emitter_Search_Geolocation.pdf", "10.1109/TVT.2022.3231398"),
    ("Zhou2014_Weighted_Intersections_IEEE.pdf", "10.1109/ICIF.2014.6916187"),
    ("Galceran2013_RAS_Survey_CPP.pdf", "10.1016/j.robot.2013.09.004"),
]

for name, doi in scihub_jobs:
    dest = os.path.join(OUT, name)
    if is_pdf(dest):
        print(f"SKIP exists\t{name}")
        continue
    print(f"=== SCIHUB {name} DOI={doi} ===")
    ok_any = False
    for url in scihub_urls(doi):
        print(f"TRY\t{url}")
        ok, msg = fetch(url, dest, timeout=50)
        print(f"  -> {msg}")
        if ok:
            ok_any = True
            break
        if "not_pdf" in msg:
            ok2, msg2 = extract_pdf_from_html(url, dest)
            print(f"  html-extract -> {msg2}")
            if ok2:
                ok_any = True
                break
        time.sleep(0.6)
    if not ok_any:
        print(f"FAIL\t{name}")

print("DONE")
