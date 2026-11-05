#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Weekend-only increment for the Swarm Alignment Hackathon 2026.

This script is deliberately gated on the sprint window. It refuses to write
"weekend" results before 2026-11-06 (Beijing), so no measurement can be
back-dated. The code is pre-existing; the DATA it produces during the sprint
is the weekend contribution.

Commands:
    python weekend_increment.py --smoke   # run a tiny sweep, write nothing
    python weekend_increment.py --full    # sweep + patch REPORT.md + rebuild PDF + sync

Standard library only. No network calls except the two repo mirrors at --full.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
SPRINT_START = dt.datetime(2026, 11, 6, 0, 0)   # Beijing local, conservative
SIZES = (5, 8, 12, 16, 20)
SEEDS = tuple(range(1, 9))
REPORT_MD = os.path.join(ROOT, "REPORT.md")
REPORT_PDF = os.path.join(ROOT, "REPORT.pdf")
RESULTS_JSON = os.path.join(ROOT, "WEEKEND_RESULTS.json")
MD2PDF = os.path.join(PROJECT, "md2pdf", "md2pdf.py")

APPENDIX_C_HEAD = "## Appendix C - Weekend-work increment: swarm-size sweep (5-20 agents)"
APPENDIX_B_ANCHOR = ("The work prepared for this sprint is this research report, its abstract, the\n"
                     "Limitations and Dual-Use / Ethical Considerations appendix, and a fresh\n"
                     "independent re-verification of all quoted numbers (5 November 2026: `RESULT: 235")


def gate():
    now = dt.datetime.now()
    if now < SPRINT_START:
        print("ABORT: sprint window has not started (now=%s, opens=%s)."
              % (now.isoformat(timespec="minutes"), SPRINT_START.isoformat()))
        print("No weekend data was written. Re-run on or after 2026-11-06.")
        return False
    return True


def sweep(sizes=SIZES, seeds=SEEDS):
    from swarmbox.fidelity import compare
    rows = []
    for n in sizes:
        r = compare(n=n, seeds=seeds)
        f = r["families"]
        rows.append({
            "n": n,
            "seeds": len(seeds),
            "cheap_collapse_rate": f["cheap"]["collapse_rate"],
            "frontier_collapse_rate": f["frontier"]["collapse_rate"],
            "collapse_gap": r["divergence"]["collapse_rate"],
            "gini_gap": r["divergence"]["gini"],
            "escape_successes": sum(f[k]["escape_successes"] for k in ("cheap", "frontier", "mixed")),
            "invariant_violations": sum(f[k]["invariant_violations"] for k in ("cheap", "frontier", "mixed")),
        })
        print("  n=%-3d cheap=%.2f frontier=%.2f gap=%.2f gini_gap=%.4f escapes=%d inv=%d"
              % (rows[-1]["n"], rows[-1]["cheap_collapse_rate"],
                 rows[-1]["frontier_collapse_rate"], rows[-1]["collapse_gap"],
                 rows[-1]["gini_gap"], rows[-1]["escape_successes"],
                 rows[-1]["invariant_violations"]))
    return rows


def verdict(rows):
    all_gap_one = all(abs(r["collapse_gap"] - 1.0) < 1e-9 for r in rows)
    zero_esc = all(r["escape_successes"] == 0 for r in rows)
    zero_inv = all(r["invariant_violations"] == 0 for r in rows)
    if all_gap_one:
        s = ("The categorical cheap/frontier gap (collapse rate 1.00 vs 0.00) survives every "
             "swarm size tested, from 5 to 20 agents: the gap is 1.00 at all five sizes. "
             "It is therefore not an artefact of the default 12-agent configuration.")
    else:
        exceptions = [str(r["n"]) for r in rows if abs(r["collapse_gap"] - 1.0) > 1e-9]
        s = ("The cheap/frontier collapse gap is not constant across swarm size; "
             "sizes with a gap below 1.00: %s." % (", ".join(exceptions) or "none"))
    s += (" Across all %d runs there were %d escape successes and %d invariant violations."
          % (sum(r["seeds"] for r in rows) * 3,
             sum(r["escape_successes"] for r in rows),
             sum(r["invariant_violations"] for r in rows)))
    if zero_esc and zero_inv:
        s += " Containment and arithmetic invariants hold at every size."
    return s


def appendix_c(rows, when):
    lines = [
        "",
        "**Generated during the sprint window, %s (Beijing).** This appendix is new work "
        "performed for the hackathon; the core code is pre-existing and is declared in "
        "Appendix B. Command: `python weekend_increment.py --full`. Raw measurements: "
        "`WEEKEND_RESULTS.json`." % when.strftime("%d %B %Y %H:%M"),
        "",
        "Track 1 asks for environments with 5-20 agents. The original experiments used a "
        "single population size (12). Here we sweep n = 5, 8, 12, 16 and 20, running the "
        "cheap, frontier and mixed families over the same eight seeds at each size, to test "
        "whether the E4 result is an artefact of one configuration.",
        "",
        "| agents n | cheap collapse | frontier collapse | collapse gap | gini gap | escapes | invariant violations |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %d | %.2f | %.2f | %.2f | %.4f | %d | %d |"
                     % (r["n"], r["cheap_collapse_rate"], r["frontier_collapse_rate"],
                        r["collapse_gap"], r["gini_gap"], r["escape_successes"],
                        r["invariant_violations"]))
    lines += ["", "**Result.** " + verdict(rows), "",
              "**Limitations of this increment.** It reuses the deterministic policies and "
              "one regeneration model; no language model is called, and the sweep changes "
              "population size only. It establishes scale-robustness inside this testbed, "
              "not scale-robustness in real LLM swarms.", ""]
    return "\n".join(lines) + "\n"


def patch_report(section, when):
    src = open(REPORT_MD, encoding="utf-8").read()
    # idempotent: drop a previous Appendix C
    src = re.sub(r"\n" + re.escape(APPENDIX_C_HEAD) + r".*?(?=\n## References)",
                 "", src, flags=re.S)
    if "## References" not in src:
        raise RuntimeError("REPORT.md has no References heading")
    src = src.replace("## References", section + "\n## References", 1)
    note = ("Appendix C (generated %s) adds a new 5-20 agent scale sweep run during the "
            "sprint window; the measurements in it are weekend work, the harness is not."
            % when.strftime("%d %B %Y"))
    if "Appendix C (generated" not in src:
        idx = src.find("## Appendix B - Pre-existing Work Disclosure")
        if idx >= 0:
            end = src.find("\n## References", idx)
            if end > 0:
                src = src[:end] + "\n" + note + "\n" + src[end:]
    open(REPORT_MD, "w", encoding="utf-8").write(src)


def rebuild_pdf():
    r = subprocess.run([sys.executable, MD2PDF, "REPORT.md", "-o", "REPORT.pdf"],
                       cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip())
    if r.returncode != 0:
        raise RuntimeError("md2pdf failed")


def validate():
    b = open(REPORT_PDF, "rb").read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", b))
    src = open(REPORT_MD, encoding="utf-8").read()
    abstract = src.split("## Abstract", 1)[1].split("---", 1)[0]
    words = len(re.findall(r"[A-Za-z0-9()\-/]+", abstract))
    checks = {
        "pdf header": b.startswith(b"%PDF-"),
        "pdf eof": b.rstrip().endswith(b"%%EOF"),
        "pages <= 10 (appendices excluded from 8-page cap)": pages <= 10,
        "abstract 150-250 words": 150 <= words <= 250,
        "authors": "**Author:** Yilang Zhi" in src,
        "dual-use appendix": "Appendix A - Limitations and Dual-Use / Ethical Considerations" in src,
        "preexisting appendix": "Appendix B - Pre-existing Work Disclosure" in src,
        "weekend appendix": APPENDIX_C_HEAD in src,
        "references": "## References" in src,
    }
    print("  PDF %d bytes, %d pages, abstract %d words" % (len(b), pages, words))
    for k, v in checks.items():
        print("   ", "OK " if v else "FAIL", k)
    if not all(checks.values()):
        raise RuntimeError("report validation failed")
    return len(b), pages, words


def github_sync():
    pat_path = os.path.join(os.path.expanduser("~"), ".github_pat")
    if not os.path.exists(pat_path):
        print("  GitHub PAT missing, skipped"); return
    pat = open(pat_path, encoding="utf-8").read().strip()
    base = "https://api.github.com/repos/Zhiyilang/swarmbox/contents/"

    def api(method, path, body=None, raw=False):
        h = {"Authorization": "Bearer " + pat, "User-Agent": "swarmbox-weekend",
             "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"}
        req = urllib.request.Request(base + path,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     method=method, headers=h)
        with urllib.request.urlopen(req, timeout=70) as r:
            return r.read(), r.status

    for name in ("REPORT.md", "REPORT.pdf", "WEEKEND_RESULTS.json"):
        local = open(os.path.join(ROOT, name), "rb").read()
        sha = None
        try:
            sha = json.loads(api("GET", name)[0])["sha"]
        except Exception:
            pass
        body = {"message": "Weekend increment: 5-20 agent scale sweep + rebuilt report",
                "content": base64.b64encode(local).decode(), "branch": "main"}
        if sha:
            body["sha"] = sha
        try:
            api("PUT", name, body)
            back = api("GET", name, raw=True)[0]
            print("   GitHub", name, "OK" if back == local else "MISMATCH")
        except urllib.error.HTTPError as e:
            print("   GitHub", name, "FAIL", e.code, e.read()[:120])


def gitee_sync():
    tool = os.path.join(PROJECT, "_gitee_push.py")
    if not os.path.exists(tool):
        print("  _gitee_push.py missing, skipped"); return
    r = subprocess.run([sys.executable, tool, "--repos", "swarmbox", "--force",
                        "--sleep", "1.0"], cwd=PROJECT, capture_output=True, text=True)
    tail = [l for l in (r.stdout or "").splitlines() if "swarmbox" in l or "failed" in l]
    print("   Gitee:", " | ".join(tail[-3:]) or ("rc=%d" % r.returncode))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="tiny sweep, no writes, no gate")
    ap.add_argument("--full", action="store_true", help="full sweep + report + sync")
    args = ap.parse_args()
    if not (args.smoke or args.full):
        ap.error("use --smoke or --full")

    if args.smoke:
        print("SMOKE (no writes):")
        rows = sweep(sizes=(5,), seeds=(1,))
        print("  verdict:", verdict(rows))
        print("SMOKE ok - experiment harness runs.")
        return 0

    if not gate():
        return 2
    now = dt.datetime.now()
    print("FULL sweep at", now.isoformat(timespec="seconds"))
    rows = sweep()
    payload = {"generated_at": now.isoformat(timespec="seconds"),
               "config": {"sizes": list(SIZES), "seeds": list(SEEDS),
                          "command": "python weekend_increment.py --full"},
               "rows": rows, "verdict": verdict(rows)}
    open(RESULTS_JSON, "w", encoding="utf-8").write(json.dumps(payload, indent=2) + "\n")
    patch_report(appendix_c(rows, now), now)
    rebuild_pdf()
    validate()
    print("Syncing both public mirrors...")
    github_sync()
    gitee_sync()
    print("DONE. Verdict:", verdict(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
