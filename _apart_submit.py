#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmatic submission of the SwarmBox project to the Apart sprint form.

The submission form is a Next.js server-action form embedded in
https://apartresearch.com/sprints/swarm-alignment-2026 (multipart/form-data).
It needs no login and no captcha; the only bot guard is the `leave_blank`
honeypot, which we leave empty.

*** HOW THE PDF REALLY WORKS (reverse-engineered from the shipped JS bundles,
    2026-11-06) ***

The "PDF File" input is rendered `disabled` and the page says
"Uploading files needs JavaScript". The client code does this:

  1. POST /api/forms/upload  {"type":"blob.generate-presigned-url", ...}
     -> {"presignedUrlPayload": {delegationToken, signature, params}}
  2. PUT the PDF bytes to the Vercel Blob API using that payload
     -> {"url": "https://...public.blob.vercel-storage.com/submissions/..."}
  3. formData.set("PDF File", thatUrl)      # a STRING, not a File
  4. dispatch the server action with the multipart FormData

On the server, readValues() does String(formData.get(key)) for EVERY field,
including file fields, and buildSchema() validates file fields as plain
strings (maxLength 1000, required -> min(1)). So sending the PDF as a raw
multipart file part is WRONG; the server would see "[object File]" or an
empty value. The old version of this script did exactly that.

This script therefore:
  * uploads the PDF via the official presigned endpoint (primary path),
  * falls back to the public, byte-identical Gitee raw URL if the upload
    endpoint is closed/unavailable (the server only requires a non-empty
    string <= 1000 chars, and judges can open the link),
  * submits the form ONCE with "PDF File" as a string field, plus the
    `_ref` reference code the client always adds.

SAFETY: the official rules say the PDF cannot be replaced after submission.
Therefore this script POSTs AT MOST ONCE per checkout. A marker file records
the attempt; any later --submit is refused. Use --check / --verify /
--upload-only freely.

    python _apart_submit.py --dry-run        # build the exact request, send nothing
    python _apart_submit.py --check          # is the project already submitted?
    python _apart_submit.py --probe          # is the upload gate open? (no upload, no side effects)
    python _apart_submit.py --upload-only    # verify the upload path ONLY (no submission)
    python _apart_submit.py --submit         # POST once (blocked before sprint opens)
    python _apart_submit.py --verify         # confirmation email + website listing

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email
import email.header
import hashlib
import http.cookiejar
import json
import os
import poplib
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PROJECT = os.path.dirname(os.path.abspath(__file__))
SWARM = os.path.join(PROJECT, "swarmbox")
STATE = os.path.join(PROJECT, ".workbuddy")
os.makedirs(STATE, exist_ok=True)
MARKER = os.path.join(STATE, "swarm_submit_attempted.json")
FIELD_CACHE = os.path.join(STATE, "apart_form_fields.json")
PDF_URL_CACHE = os.path.join(STATE, "apart_pdf_url.json")
SPRINT_URL = "https://apartresearch.com/sprints/swarm-alignment-2026"
UPLOAD_URL = "https://apartresearch.com/api/forms/upload"
BLOB_API = "https://vercel.com/api/blob"
SPRINT_START = dt.datetime(2026, 11, 6, 20, 0)  # Beijing = AoE 2026-11-06 00:00 (UTC-12)
DEADLINE = dt.datetime(2026, 11, 9, 19, 59)        # Beijing local

FORM_ID = "project-submission"
SPRINT_SLUG = "swarm-alignment-2026"
PDF_FIELD = "PDF File"
PDF_FILENAME = "SwarmBox-REPORT.pdf"
# Public, anonymous, byte-identical fallback (verified HTTP 200 on 2026-11-06).
FALLBACK_PDF_URL = "https://gitee.com/ZhiYIlang/swarmbox/raw/master/REPORT.pdf"

MAIL_USER = "2383844705@qq.com"
MAIL_AUTH_FILE = os.path.join(STATE, "qqmail.env")

TITLE = "SwarmBox"
TEAM = "SwarmBox"
LOCATION = "Shanghai, China"
NAME = "Yilang Zhi"
EMAIL_ADDR = "2383844705@qq.com"
CODE_URL = "https://github.com/Zhiyilang/swarmbox"
EXTRA_URL = "https://gitee.com/Zhiyilang/swarmbox"

# Field names are taken verbatim from the live form. Note the trailing space
# in "ProjectSummary_Framer " - it is part of the real name.
F = {
    "ProjectTitle_Framer": TITLE,
    "ProjectSummary_Framer ": None,      # filled from REPORT.md Abstract
    "InterestedInPublishing_Framer": "Yes",
    "Tracks": "Track 1",
    "Presentation_Framer": "",
    "Code_Framer": CODE_URL,
    "AdditionalLink_Framer": EXTRA_URL,
    "TeamName_Framer": TEAM,
    "Location_Framer": LOCATION,
    "Member1_Name_Framer": NAME,
    "Member1_Email_Framer": EMAIL_ADDR,
    "Member1_Discord_Framer": "",
    "Member1_Scholar_Framer": "",
    "leave_blank": "",
}

REF_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"   # Crockford base32, matches the client
SUCCESS_HINTS = ("thank you", "submission received", "submitted", "success",
                 "we've received", "your project has been")


def abstract_from_report():
    src = open(os.path.join(SWARM, "REPORT.md"), encoding="utf-8").read()
    text = src.split("## Abstract", 1)[1].split("---", 1)[0]
    text = re.sub(r"^>\s?", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    words = len(re.findall(r"[A-Za-z0-9()\-/]+", text))
    if not (150 <= words <= 250):
        raise RuntimeError("abstract is %d words, official range is 150-250" % words)
    return text, words


def report_data_is_sprint_safe():
    """Refuse to submit any report whose 'weekend work' was generated pre-sprint."""
    src = open(os.path.join(SWARM, "REPORT.md"), encoding="utf-8").read()
    claims = ("Appendix C - Weekend-work" in src
              or "Generated during the sprint window" in src)
    if not claims:
        return True, "clean base report, no weekend-work claim"
    jp = os.path.join(SWARM, "WEEKEND_RESULTS.json")
    if not os.path.exists(jp):
        return False, "report claims weekend work but WEEKEND_RESULTS.json is missing"
    try:
        gen = dt.datetime.fromisoformat(json.load(open(jp, encoding="utf-8"))["generated_at"])
    except Exception as e:
        return False, "cannot parse generated_at (%s)" % e
    if gen < SPRINT_START:
        return False, ("PRE-SPRINT DATA %s < sprint start %s (AoE 11-06 00:00)"
                       % (gen.isoformat(timespec="seconds"), SPRINT_START.isoformat()))
    return True, "weekend data generated %s, inside sprint window" % gen.isoformat(timespec="seconds")


def _get(url, opener=None, tries=4, timeout=45):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            fh = opener.open(req, timeout=timeout) if opener else urllib.request.urlopen(req, timeout=timeout)
            with fh as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            if k + 1 < tries:
                time.sleep(2 + 2 * k)
    raise last


def _unescape(s):
    import html as H
    return H.unescape(s)


def fetch_form(opener, allow_cache=False):
    """Return (html, hidden_fields, from_cache). Live tokens are mandatory for --submit."""
    cached = False
    try:
        html = _get(SPRINT_URL, opener)
    except Exception as e:
        if allow_cache and os.path.exists(FIELD_CACHE):
            d = json.load(open(FIELD_CACHE, encoding="utf-8"))
            print("WARN: live fetch failed (%s); using cached fields from %s"
                  % (type(e).__name__, d.get("at")))
            return "", d["hidden"], True
        raise
    anchor = 'action="/sprints/swarm-alignment-2026#submission-swarm-alignment-2026-status"'
    i = html.find(anchor)
    if i < 0:
        raise RuntimeError("submission form not found on sprint page")
    start = html.rfind("<form", 0, i)
    end = html.find("</form>", i)
    frag = html[start:end]
    hidden = {}
    for tag in re.findall(r'<input[^>]*type="hidden"[^>]*>', frag):
        n = re.search(r'name="([^"]+)"', tag)
        v = re.search(r'value="([^"]*)"', tag)
        if n:
            hidden[n.group(1)] = _unescape(v.group(1)) if v else ""
    for key in ("$ACTION_REF_6", "$ACTION_6:0", "$ACTION_6:1", "$ACTION_KEY"):
        if key not in hidden:
            raise RuntimeError("missing server-action field " + key)
    json.dump({"at": dt.datetime.now().isoformat(timespec="seconds"),
               "hidden": hidden}, open(FIELD_CACHE, "w", encoding="utf-8"), indent=2)
    return html, hidden, cached


# ---------------------------------------------------------------------------
# Step 1-2: upload the PDF through the official presigned endpoint.
# ---------------------------------------------------------------------------
def _store_id(delegation_token):
    """The client derives storeId from the first (base64url JSON) segment."""
    head = delegation_token.split(".", 1)[0]
    b64 = head.replace("-", "+").replace("_", "/")
    b64 += "=" * (-len(b64) % 4)
    try:
        import base64
        obj = json.loads(base64.b64decode(b64).decode("utf-8"))
        sid = obj.get("storeId", "")
        return sid[6:] if str(sid).startswith("store_") else str(sid)
    except Exception:
        return ""


def request_upload_token(opener, pathname):
    """POST /api/forms/upload for a presigned URL payload (no blob is created)."""
    client_payload = json.dumps({"form": FORM_ID, "slug": SPRINT_SLUG, "key": PDF_FIELD},
                                separators=(",", ":"))
    body = json.dumps({"type": "blob.generate-presigned-url",
                       "payload": {"pathname": pathname,
                                   "clientPayload": client_payload,
                                   "multipart": False}}, separators=(",", ":")).encode()
    req = urllib.request.Request(
        UPLOAD_URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
                 "Origin": "https://apartresearch.com", "Referer": SPRINT_URL,
                 "Accept": "*/*"})
    try:
        with opener.open(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("upload token HTTP %d: %s"
                           % (e.code, e.read()[:200].decode("utf-8", "replace")))


def upload_pdf_presigned(opener, pdf_bytes):
    """Upload via /api/forms/upload + Vercel Blob PUT. Return the public URL.

    This does NOT create a submission record; it only stores a blob. It is
    safe to call with --upload-only before the real submission.
    """
    pathname = "submissions/%s/%s" % (SPRINT_SLUG, PDF_FILENAME)
    data = request_upload_token(opener, pathname)
    pp = data.get("presignedUrlPayload")
    if not pp:
        raise RuntimeError("no presignedUrlPayload in response: %s" % str(data)[:200])
    params = {"pathname": pathname}
    params.update(pp.get("params") or {})
    params["vercel-blob-delegation"] = pp["delegationToken"]
    params["vercel-blob-signature"] = pp["signature"]
    put_url = BLOB_API + "/?" + urllib.parse.urlencode(params)
    headers = {"Content-Type": "application/pdf", "User-Agent": "Mozilla/5.0",
               "x-api-version": "12", "x-api-blob-request-attempt": "0",
               "x-api-blob-request-id": hashlib.sha256(
                   (str(time.time()) + secrets.token_hex(8)).encode()).hexdigest()[:32],
               "x-vercel-blob-store-id": _store_id(pp["delegationToken"]),
               "x-content-length": str(len(pdf_bytes))}
    put = urllib.request.Request(put_url, data=pdf_bytes, method="PUT", headers=headers)
    try:
        with opener.open(put, timeout=90) as r:
            out = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("blob PUT HTTP %d: %s"
                           % (e.code, e.read()[:200].decode("utf-8", "replace")))
    url = out.get("url") or out.get("downloadUrl")
    if not url or not url.startswith("http"):
        raise RuntimeError("blob PUT returned no usable url: %s" % str(out)[:200])
    return url


def resolve_pdf_url(opener, pdf_bytes, allow_fallback=True):
    """Primary: official presigned upload. Fallback: public Gitee raw URL.

    Returns (url, method, note). Never raises for a closed upload form when
    allow_fallback is True - the fallback is a legitimate string value.
    """
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        url = upload_pdf_presigned(opener, pdf_bytes)
        rec = {"at": dt.datetime.now().isoformat(timespec="seconds"),
               "url": url, "method": "presigned-upload", "pdf_sha256": sha}
        json.dump(rec, open(PDF_URL_CACHE, "w", encoding="utf-8"), indent=2)
        return url, "presigned-upload", "official Vercel Blob upload succeeded"
    except Exception as e:
        note = "presigned upload unavailable (%s: %s)" % (type(e).__name__, str(e)[:160])
    if not allow_fallback:
        raise RuntimeError(note)
    # A URL is exactly what the official client puts in this field.
    return FALLBACK_PDF_URL, "fallback-public-url", note + "; using public byte-identical raw URL"


def build_multipart(hidden, pdf_url, ref):
    """All fields are plain strings - including "PDF File" (a URL)."""
    boundary = "----swarmbox" + secrets.token_hex(12)
    chunks = []

    def field(name, value):
        chunks.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                       % (boundary, name, value)).encode("utf-8"))

    for k, v in hidden.items():
        field(k, v)
    for k, v in F.items():
        field(k, v)
    field("_ref", ref)
    field(PDF_FIELD, pdf_url)
    chunks.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary


def mail_auth():
    for line in open(MAIL_AUTH_FILE, encoding="utf-8"):
        if line.startswith("QQMAIL_AUTH="):
            return line.strip().split("=", 1)[1]
    raise RuntimeError("QQMAIL_AUTH missing")


def recent_mail_subjects(limit=40):
    p = poplib.POP3_SSL("pop.qq.com", 995, timeout=45)
    p.user(MAIL_USER)
    p.pass_(mail_auth())
    n, _ = p.stat()
    out = []
    for i in range(max(1, n - limit), n + 1):
        try:
            lines = p.top(i, 0)[1]
            m = email.message_from_string(b"\r\n".join(lines).decode("utf-8", "replace"))
            def dec(s):
                try:
                    return str(email.header.make_header(email.header.decode_header(s or "")))
                except Exception:
                    return s or ""
            out.append((dec(m.get("From", "")), dec(m.get("Subject", ""))))
        except Exception:
            pass
    p.quit()
    return out


def website_has_project():
    """Only an actual project-listing link counts as evidence of submission.

    A bare "SwarmBox" word in marketing copy / the schedule / a track
    description must NOT be read as "already submitted" -- that would make
    the daily automation silently skip the POST and lose the whole entry.
    Verified 2026-11-06 02:2x against the live sprint page (NOT_SUBMITTED).
    """
    try:
        s = _get(SPRINT_URL)
        listed = bool(re.search(r"/sprints/projects/[^\\\"'<>\\s]*" +
                                re.escape(TITLE.lower()), s.lower()))
        return listed, len(s)
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, str(e)[:120])


def external_evidence():
    hits = [(f, s) for f, s in recent_mail_subjects()
            if "swarmbox" in (f + " " + s).lower() or
            ("confirm" in s.lower() and "apart" in f.lower())]
    on_site, info = website_has_project()
    return hits, on_site, info


def already_submitted(verbose=True):
    if os.path.exists(MARKER):
        d = json.load(open(MARKER, encoding="utf-8"))
        if d.get("result") == "failed":
            hits, on_site, info = external_evidence()
            if hits or on_site:
                if verbose:
                    print("Previous POST failed, but the project is visible:", hits[-2:], info)
                return True
            if verbose:
                print("Previous POST failed with no independent evidence; retry is allowed.")
            return False
        if verbose:
            print("MARKER exists: previous POST at", d.get("at"), "| result:", d.get("result"))
        return True
    hits, on_site, info = external_evidence()
    if hits:
        if verbose:
            print("CONFIRMATION MAIL detected:", hits[-3:])
        return True
    if on_site:
        if verbose:
            print("PROJECT LISTED on sprint page:", info)
        return True
    if verbose:
        print("No prior submission detected (no marker / no confirmation mail / no listing).")
    return False


def new_ref():
    return "".join(secrets.choice(REF_ALPHABET) for _ in range(6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--upload-only", action="store_true",
                    help="verify the PDF upload path only; never submits the form")
    ap.add_argument("--probe", action="store_true",
                    help="check whether the upload gate is open; no blob, no submission")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if not any((args.dry_run, args.check, args.upload_only, args.probe,
                args.submit, args.verify)):
        ap.error("choose one of --dry-run / --check / --probe / --upload-only "
                 "/ --submit / --verify")

    if args.check:
        print("ALREADY_SUBMITTED" if already_submitted() else "NOT_SUBMITTED")
        return 0

    if args.verify:
        mail_hits = [(f, s) for f, s in recent_mail_subjects(60)
                     if "swarmbox" in (f + " " + s).lower()]
        on_site, info = website_has_project()
        print("confirmation_mail:", mail_hits[-3:] if mail_hits else "NONE")
        print("website_listing:", on_site, info)
        ok = bool(mail_hits) or on_site
        print("VERIFY_OK" if ok else "VERIFY_FAIL")
        return 0 if ok else 1

    abstract, words = abstract_from_report()
    F["ProjectSummary_Framer "] = abstract
    pdf_path = os.path.join(SWARM, "REPORT.pdf")
    pdf = open(pdf_path, "rb").read()
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError("REPORT.pdf is not a PDF")

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    if args.probe:
        # Zero side effects: ask for a token, do NOT upload a blob, do NOT submit.
        print("PROBE (no blob created, no submission sent)")
        pathname = "submissions/%s/%s" % (SPRINT_SLUG, PDF_FILENAME)
        try:
            d = request_upload_token(opener, pathname)
            print("GATE_OPEN   : presignedUrlPayload present:", bool(d.get("presignedUrlPayload")))
            return 0
        except Exception as e:
            msg = str(e)
            print("GATE_CLOSED :", msg[:250])
            if "form closed" in msg:
                print("Reason      : server-side time gate (sprint not yet open)")
            return 1

    if args.upload_only:
        # Zero-risk: only stores a blob / proves the gate is open. No form POST.
        print("UPLOAD-ONLY (no submission will be sent)")
        try:
            url = upload_pdf_presigned(opener, pdf)
            print("UPLOAD_OK   :", url)
            return 0
        except Exception as e:
            print("UPLOAD_FAIL :", type(e).__name__, str(e)[:250])
            return 1

    page_html, hidden, cached = fetch_form(opener, allow_cache=args.dry_run)
    if args.submit and cached:
        print("ABORT: refusing to submit with cached server-action fields."); return 2

    if args.dry_run:
        # Do not upload anything in dry-run: show the exact field layout.
        demo_url = FALLBACK_PDF_URL
        body, ctype = build_multipart(hidden, demo_url, "DEMO00")
        print("Form URL      :", SPRINT_URL)
        print("Field source  :", "CACHE" if cached else "LIVE")
        print("Abstract      :", words, "words")
        print("PDF bytes     :", len(pdf), "(uploaded at submit time, NOT as a file part)")
        print("PDF File value:", demo_url, "(string, <=1000 chars:",
              len(demo_url) <= 1000, ")")
        print("Hidden fields :", list(hidden.keys()))
        print("Payload fields:", len(hidden) + len(F) + 2, "| body", len(body), "bytes")
        print("Submit button :", "Submit project" if "Submit project" in page_html else "NOT FOUND")
        safe, why = report_data_is_sprint_safe()
        print("Data check    :", "SAFE" if safe else "UNSAFE", "-", why)
        print("DRY RUN - nothing was sent.")
        return 0

    if args.submit:
        safe, why = report_data_is_sprint_safe()
        if not safe:
            print("ABORT: report carries pre-sprint data; no POST sent."); return 2
        now = dt.datetime.now()
        if now < SPRINT_START:
            print("ABORT: sprint has not started; no POST sent."); return 2
        if now > DEADLINE:
            print("ABORT: deadline passed; no POST sent."); return 2
        if already_submitted():
            print("ABORT: already submitted; refusing a second POST (PDF cannot be replaced).")
            return 3

        # Step 1-2: get the PDF URL. Never POST without one.
        pdf_url, method, note = resolve_pdf_url(opener, pdf, allow_fallback=True)
        print("PDF URL       :", pdf_url)
        print("PDF method    :", method, "|", note)
        if len(pdf_url) > 1000:
            print("ABORT: PDF URL exceeds the 1000-char server limit."); return 2

        body, ctype = build_multipart(hidden, pdf_url, new_ref())
        print("Form URL      :", SPRINT_URL)
        print("Field source  :", "CACHE (dry-run only)" if cached else "LIVE")
        print("Abstract      :", words, "words")
        print("Hidden fields :", list(hidden.keys()))
        print("Payload fields:", len(hidden) + len(F) + 2, "| body", len(body), "bytes")
        print("Submit button :", "Submit project" if "Submit project" in page_html else "NOT FOUND")

        req = urllib.request.Request(
            SPRINT_URL, data=body, method="POST",
            headers={"User-Agent": "Mozilla/5.0",
                     "Content-Type": ctype,
                     "Accept": "text/html,application/xhtml+xml,*/*",
                     "Referer": SPRINT_URL,
                     "Origin": "https://apartresearch.com"})
        stamp = now.strftime("%Y%m%d_%H%M%S")
        status, final_url, err = None, SPRINT_URL, None
        try:
            with opener.open(req, timeout=90) as r:
                raw = r.read()
                status = r.status
                final_url = r.geturl()
        except urllib.error.HTTPError as e:
            raw = e.read(); status = e.code
        except Exception as e:
            raw = b""; err = "%s: %s" % (type(e).__name__, str(e)[:200])
        out = os.path.join(STATE, "swarm_submit_response_%s.html" % stamp)
        open(out, "wb").write(raw)
        text = raw.decode("utf-8", "replace")
        low = text.lower()
        hints = [h for h in SUCCESS_HINTS if h in low]
        ok_http = status is not None and 200 <= status < 300
        record = {"at": now.isoformat(timespec="seconds"), "http_status": status,
                  "final_url": final_url, "response_bytes": len(raw),
                  "response_file": out, "success_hints": hints, "error": err,
                  "pdf_url": pdf_url, "pdf_method": method,
                  "result": "likely-submitted" if ok_http else "failed"}
        json.dump(record, open(MARKER, "w", encoding="utf-8"), indent=2)
        print("POST status   :", status, "| bytes", len(raw), "| url", final_url)
        if err:
            print("POST error    :", err)
        print("Success hints :", hints)
        print("Result        :", record["result"])
        print("Response saved:", out)
        print("NEXT: run --verify after ~5 minutes. Do NOT POST again by hand.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
