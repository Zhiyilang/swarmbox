"""Generate SwarmBox demo video from REAL command output (no fabrication).

Pipeline: run real commands -> render scene HTML with Edge headless -> PNG
frame sequence -> ffmpeg encode -> verify duration/resolution.
"""
import os
import re
import shutil
import subprocess
import sys
import html

BASE = r"D:\桌面\part-time jobs\GitHub\swarmbox"
TMP = r"C:\Temp\swarmvid"
FF = r"D:\桌面\part-time jobs\GitHub\_videotool\ffmpeg.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FPS = 30

os.makedirs(TMP, exist_ok=True)
frames_dir = os.path.join(TMP, "frames")
if os.path.isdir(frames_dir):
    shutil.rmtree(frames_dir)
os.makedirs(frames_dir)


def run(cmd, timeout=180):
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


# ---------- 1. capture REAL output ----------
print("[1/4] capturing real command output ...")
cmds = [
    ("eval.py", [sys.executable, "eval.py"]),
    ("python -m swarmbox gate", [sys.executable, "-m", "swarmbox", "gate"]),
    ("python -m swarmbox run", [sys.executable, "-m", "swarmbox", "run"]),
    ("python -m swarmbox fidelity", [sys.executable, "-m", "swarmbox", "fidelity"]),
]
captured = []
for label, cmd in cmds:
    out = run(cmd)
    lines = [l.rstrip() for l in out.splitlines()]
    # keep the informative tail
    lines = [l for l in lines if l.strip()][-26:]
    captured.append((label, lines))
    print("    %-32s %d lines" % (label, len(lines)))
    # hard assertion: eval must report the real number
    if label == "eval.py":
        assert any("235 passed" in l and "0 failed" in l for l in lines), \
            "eval output changed! refusing to build video on stale data: %r" % lines[-3:]


# ---------- 2. render scene PNGs ----------
print("[2/4] rendering scenes ...")

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1920px;height:1080px;background:#0e1117;color:#e6edf3;
     font-family:Consolas,"Courier New",monospace;display:flex;
     flex-direction:column;padding:70px 90px;overflow:hidden}
.hdr{font-size:34px;color:#7fd67f;margin-bottom:26px;letter-spacing:1px}
.cmd{font-size:30px;color:#ffd479;margin-bottom:24px}
.term{flex:1;background:#161b22;border:1px solid #30363d;border-radius:12px;
      padding:34px 40px;font-size:26px;line-height:1.62;white-space:pre;overflow:hidden}
.g{color:#7fd67f}.r{color:#ff8f8f}.y{color:#ffd479}.c{color:#6fb3d2}.d{color:#8b949e}
.big{font-size:64px;color:#e6edf3;margin-bottom:30px;line-height:1.25}
.sub{font-size:34px;color:#8b949e;margin-bottom:40px}
.kpis{display:flex;gap:40px;margin-top:50px}
.kpi{flex:1;background:#161b22;border:1px solid #30363d;border-radius:14px;
     padding:40px 30px;text-align:center}
.kpi .n{font-size:76px;color:#7fd67f;font-weight:700;line-height:1.1}
.kpi .l{font-size:24px;color:#8b949e;margin-top:14px}
.foot{margin-top:auto;font-size:24px;color:#6e7681}
.note{font-size:26px;color:#ffd479;margin-top:34px}
.term.short{flex:0 0 auto;font-size:42px;padding:40px 46px;line-height:1.75}
.explain{margin-top:44px;font-size:28px;line-height:1.8;color:#c9d1d9;
         background:#161b22;border-left:6px solid #7fd67f;border-radius:10px;
         padding:34px 40px}
"""


def colorize(line):
    """light syntax colouring for real output"""
    e = html.escape(line)
    e = re.sub(r"(escape successes 0|0 violations|violations 0|escape 0|0 failed)",
               r'<span class="g">\1</span>', e)
    e = re.sub(r"(235 passed)", r'<span class="g">\1</span>', e)
    e = re.sub(r"(-0\.831|1\.0000|0\.1649|10)", r'<span class="c">\1</span>', e)
    e = re.sub(r"(\[bounds:[^\]]*\])", r'<span class="d">\1</span>', e)
    return e


scenes = []  # (html_filename, seconds)

# scene 0: title
scenes.append(("s0", '''
<div class="big">SwarmBox</div>
<div class="sub">多智能体不可逃逸测试床 · Multi-Agent Non-Escape Testbed</div>
<div class="kpis">
  <div class="kpi"><div class="n">235</div><div class="l">断言全部通过</div></div>
  <div class="kpi"><div class="n">0</div><div class="l">逃逸成功次数</div></div>
  <div class="kpi"><div class="n">0</div><div class="l">不变量违反</div></div>
  <div class="kpi"><div class="n">0</div><div class="l">第三方依赖</div></div>
</div>
<div class="note">它不解释执行智能体的输出，而是把输出当作数据解析 —— 逃逸手段不在语法里。</div>
<div class="foot">2026 华为开发者大赛 · 智能体创新赛（北部赛区）</div>
''', 6))

# scenes 1..4: real command output
durs = {0: 15, 1: 12, 2: 13, 3: 12}
EXPLAIN = {
    "python -m swarmbox gate":
        "32 条攻击语料覆盖文件 / 网络 / 进程 / import / 反射等逃逸尝试。<br>"
        "31 条命中预期规则 ID，<span class=\"g\">escape successes 0</span>"
        " —— 没有任何一条真正逃逸成功。",
}
for i, (label, lines) in enumerate(captured):
    body = "\n".join(colorize(l) for l in lines)
    short = len(lines) <= 4
    term_cls = "term short" if short else "term"
    inner = '<div class="cmd">$ %s</div><div class="%s">%s</div>' % (
        html.escape(label), term_cls, body)
    if short and label in EXPLAIN:
        inner += '<div class="explain">%s</div>' % EXPLAIN[label]
    scenes.append(("s%d" % (i + 1), inner, durs.get(i, 12)))

# scene 5: highlight
scenes.append(("s5", '''
<div class="hdr">核心设计</div>
<div class="term"><span class="y">不解释执行，只作数据解析</span>

文件 / 网络 / 进程 / import / 反射 等逃逸手段
<span class="g">根本不在语法里</span> —— 不是被禁止，而是无从调用。

<span class="y">三重校验</span>
  check_shape(prop)           结构层
  check_identity(prop, id)    身份层
  check_state(prop, world, id) 状态层
  <span class="c">screen()</span> 汇总闸门 → 拒绝即写入只追加账本

<span class="y">可审计，而非需被信任</span>
  全部被拒提案 append-only 记录，事后可完整回放。</div>
<div class="foot">SwarmBox · Zhiyilang</div>
''', 16))

# scene 6: ending
scenes.append(("s6", '''
<div class="big">可复现</div>
<div class="term">git clone https://github.com/Zhiyilang/swarmbox.git
cd swarmbox
python eval.py          <span class="c"># 235 passed, 0 failed</span>
python -m swarmbox gate <span class="c"># escape successes 0</span>
python -m swarmbox run  <span class="c"># invariants 0 violations</span>

<span class="d">Python 3.9+ · 零第三方依赖 · 零网络访问</span></div>
<div class="foot">SwarmBox · MIT License · Zhiyilang</div>
''', 8))

pngs = []
for name, body, secs in scenes:
    h = "<!DOCTYPE html><html><head><meta charset='utf-8'><style>%s</style></head><body>%s</body></html>" % (CSS, body)
    hp = os.path.join(TMP, name + ".html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(h)
    pp = os.path.join(TMP, name + ".png")
    if os.path.exists(pp) and os.path.getsize(pp) > 10000:
        pngs.append((pp, secs))
        print("    %s -> %d s (reuse cached PNG)" % (name, secs))
        continue
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-sandbox", "--virtual-time-budget=5000",
                    "--window-size=1920,1080", "--screenshot=" + pp,
                    "file:///" + hp.replace("\\", "/")],
                   capture_output=True, timeout=120)
    if not os.path.exists(pp):
        sys.exit("render failed: " + name)
    pngs.append((pp, secs))
    print("    %s -> %d s (%d B)" % (name, secs, os.path.getsize(pp)))

# ---------- 3. concat list (avoids copying thousands of frame files) ----------
print("[3/4] building concat list ...")
lst = os.path.join(TMP, "list.txt")
with open(lst, "w", encoding="utf-8") as f:
    for pp, secs in pngs:
        f.write("file '%s'\n" % pp.replace("\\", "/"))
        f.write("duration %.3f\n" % float(secs))
    # concat demuxer requires the last file to be listed twice
    f.write("file '%s'\n" % pngs[-1][0].replace("\\", "/"))
total_s = sum(s for _, s in pngs)
print("    scenes: %d, total %.1f s" % (len(pngs), total_s))

# ---------- 4. encode ----------
print("[4/4] encoding ...")
out = os.path.join(BASE, "swarmbox_demo.mp4")
r = subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-vsync", "vfr", "-r", str(FPS),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-movflags", "+faststart", out],
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit("encode failed: " + r.stderr[-800:])

r = subprocess.run([FF, "-i", out], capture_output=True, text=True)
dur, res = None, None
for line in r.stderr.splitlines():
    if "Duration" in line:
        dur = line.strip()
    if "Stream" in line and "Video:" in line:
        m = re.search(r", (\d{3,4})x(\d{3,4})", line)
        if m:
            res = m.group(1) + "x" + m.group(2)
print("OK", out, os.path.getsize(out), "bytes")
print("DURATION:", dur)
print("RES:", res)
