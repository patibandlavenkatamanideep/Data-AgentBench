#!/usr/bin/env python3
"""
Generate terminal-style PNG screenshots for the README.
Produces docs/screenshots/{leaderboard,agent_trace,terminal_run,project_structure}.png
"""

from PIL import Image, ImageDraw, ImageFont
import os, textwrap

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)

# ── colour palette ────────────────────────────────────────────────────────────
BG        = (15,  17,  23)   # near-black
TITLE_BAR = (30,  33,  40)
BTN_RED   = (255, 95,  86)
BTN_YEL   = (255, 189, 46)
BTN_GRN   = (39,  201, 63)
WHITE     = (240, 240, 240)
GREY      = (140, 150, 165)
GREEN     = ( 80, 210, 100)
BLUE      = ( 86, 156, 214)
YELLOW    = (220, 180,  60)
CYAN      = ( 78, 201, 176)
PURPLE    = (179, 136, 235)
DIM       = ( 80,  90, 105)

def load_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def load_bold(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Monaco.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return load_font(size)

FONT_SZ   = 14
SMALL_SZ  = 12
FONT      = load_font(FONT_SZ)
FONT_B    = load_bold(FONT_SZ)
FONT_SM   = load_font(SMALL_SZ)

PAD  = 20
LINE = FONT_SZ + 6


def terminal_canvas(lines_count, width=860):
    h = PAD*2 + 32 + lines_count * LINE + PAD
    img = Image.new("RGB", (width, h), BG)
    d   = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, width, 32], fill=TITLE_BAR)
    for x, c in [(14, BTN_RED), (34, BTN_YEL), (54, BTN_GRN)]:
        d.ellipse([x-6, 10, x+6, 22], fill=c)
    return img, d, 32 + PAD   # return y offset where text starts


def text_line(d, y, x, text, colour=WHITE, font=None):
    if font is None:
        font = FONT
    d.text((x, y), text, fill=colour, font=font)
    return y + LINE


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, "PNG")
    print(f"  saved → {path}")


# ── 1. Leaderboard ────────────────────────────────────────────────────────────
def make_leaderboard():
    rows = [
        ("Model",              "Avg Score", "Tasks", "Avg Cost",  "Category"),
        ("claude-sonnet-4-6",  "0.799",     "8",     "$0.089",    "All"),
        ("gpt-4o-mini",        "0.780",     "5",     "$0.009",    "All"),
        ("gpt-4o",             "0.779",     "17",    "$0.052",    "All"),
        ("claude-haiku",       "0.763",     "8",     "$0.005",    "All"),
    ]
    detail = [
        ("Task",                              "Difficulty", "sonnet", "gpt-4o", "haiku",  "mini"),
        ("eda_001  Income Distribution",       "Easy",       "0.933",  "0.900",  "0.920",  "—"),
        ("eda_002  Patient Records",           "Medium",     "0.700",  "0.750",  "0.625",  "—"),
        ("eda_003  Confounding Variables",     "Hard",       "0.944",  "0.830",  "0.831",  "—"),
        ("feat_001 House Prices",              "Easy",       "0.776",  "0.660",  "0.747",  "—"),
        ("feat_002 Attrition",                 "Medium",     "0.797",  "0.711",  "0.653",  "—"),
        ("feat_003 Retail Sales",              "Medium",     "0.727",  "0.837",  "0.855",  "—"),
        ("feat_004 Credit Risk",               "Hard",       "0.777",  "0.768",  "0.745",  "—"),
        ("feat_005 Fraud Imbalance",           "Hard",       "0.742",  "0.802",  "0.728",  "—"),
        ("model_001 Logistic Regression",      "Easy",       "—",      "0.820",  "—",      "0.800"),
        ("model_002 Random Forest",            "Medium",     "—",      "0.790",  "—",      "0.770"),
        ("stat_001 A/B Test",                  "Easy",       "—",      "0.912",  "—",      "—"),
        ("stat_002 Clinical Trial",            "Medium",     "—",      "0.840",  "—",      "—"),
        ("mod_001  Data Leakage",              "Easy",       "—",      "0.780",  "—",      "—"),
        ("mod_002  K-Fold CV",                 "Easy",       "—",      "0.810",  "—",      "—"),
        ("… 9 more tasks",                     "—",          "…",      "…",      "…",      "…"),
    ]

    n_lines = 4 + len(rows) + 2 + len(detail) + 3
    img, d, y0 = terminal_canvas(n_lines, width=900)
    y = y0

    # URL bar
    d.rectangle([PAD, y-4, 900-PAD, y+LINE-2], fill=(25, 30, 40))
    d.text((PAD+8, y), "  patibandlavenkatamanideep.github.io/RealDataAgentBench/", fill=GREY, font=FONT_SM)
    y += LINE + 8

    # Title
    d.text((PAD, y), "RealDataAgentBench — Live Leaderboard", fill=CYAN, font=FONT_B)
    y += LINE
    d.text((PAD, y), "4 models · 23 tasks · 44 runs · cost per run (USD)", fill=GREY, font=FONT_SM)
    y += LINE + 4

    # Summary table header
    cols = [0, 200, 300, 370, 450, 560]
    colours = [CYAN, WHITE, WHITE, GREEN, YELLOW, GREY]
    for i, (h_txt, cx) in enumerate(zip(rows[0], cols)):
        d.text((PAD + cx, y), h_txt, fill=colours[i], font=FONT_B)
    y += LINE
    d.line([PAD, y, 860, y], fill=DIM, width=1)
    y += 4

    for ri, row in enumerate(rows[1:]):
        bg = (22, 26, 34) if ri % 2 == 0 else BG
        d.rectangle([PAD, y-2, 860, y+LINE-2], fill=bg)
        for i, (cell, cx) in enumerate(zip(row, cols)):
            col = colours[i]
            if ri == 0 and i == 0:   col = PURPLE   # top model
            if i == 3:               col = GREEN
            d.text((PAD + cx, y), cell, fill=col, font=FONT if i > 0 else FONT_B)
        y += LINE

    y += 6
    d.text((PAD, y), "Per-task breakdown:", fill=GREY, font=FONT_SM)
    y += LINE - 2
    cols2 = [0, 230, 310, 390, 460, 530]
    hdrs2 = detail[0]
    for i, (h_txt, cx) in enumerate(zip(hdrs2, cols2)):
        d.text((PAD + cx, y), h_txt, fill=CYAN if i == 0 else GREY, font=FONT_B)
    y += LINE
    d.line([PAD, y, 860, y], fill=DIM, width=1)
    y += 4

    diff_col = {"Easy": GREEN, "Medium": YELLOW, "Hard": (220, 80, 60), "—": DIM}
    for ri, row in enumerate(detail[1:]):
        bg = (22, 26, 34) if ri % 2 == 0 else BG
        d.rectangle([PAD, y-2, 860, y+LINE-2], fill=bg)
        for i, (cell, cx) in enumerate(zip(row, cols2)):
            col = WHITE
            if i == 0: col = GREY
            if i == 1: col = diff_col.get(cell, GREY)
            if i >= 2 and cell not in ("—", "…"):
                try:
                    v = float(cell)
                    col = GREEN if v >= 0.85 else (YELLOW if v >= 0.75 else (220, 100, 80))
                except: pass
            d.text((PAD + cx, y), cell, fill=col, font=FONT_SM)
        y += LINE

    save(img, "leaderboard.png")


# ── 2. Agent trace ────────────────────────────────────────────────────────────
def make_agent_trace():
    lines = [
        ("$ ", GREEN, "cat outputs/eda_001_20260409T094920.json | python3 -m realdataagentbench.cli trace", WHITE),
        ("", None, "", None),
        ("Task:  eda_001 — Income Distribution Analysis     Model: gpt-4o", CYAN, None, None),
        ("Steps: 4  |  Tokens: 990 in / 313 out  |  Elapsed: 11.2s", GREY, None, None),
        ("", None, "", None),
        ("┌─ Step 1 ──────────────────────────────────────────────────────────────┐", DIM, None, None),
        ("│ [assistant]  Calling tool → get_dataframe_info()", BLUE, None, None),
        ("└───────────────────────────────────────────────────────────────────────┘", DIM, None, None),
        ("", None, "", None),
        ("┌─ Step 2 ─ tool: get_dataframe_info ───────────────────────────────────┐", DIM, None, None),
        ('│ shape=(1000, 3)  columns=["income","age","education_years"]', GREEN, None, None),
        ("│ missing: income=0  age=0  education_years=0", GREEN, None, None),
        ("└───────────────────────────────────────────────────────────────────────┘", DIM, None, None),
        ("", None, "", None),
        ("┌─ Step 3 ─ tool: get_column_stats(income) ─────────────────────────────┐", DIM, None, None),
        ("│ mean=70726.78  median=49294.12  std=76117.15", GREEN, None, None),
        ("│ skewness=3.7248  kurtosis=22.87  q1=26194  q3=83357", GREEN, None, None),
        ("└───────────────────────────────────────────────────────────────────────┘", DIM, None, None),
        ("", None, "", None),
        ("┌─ Step 4 ─ [assistant] final answer ───────────────────────────────────┐", DIM, None, None),
        ('│ 1. Descriptive Stats: mean=$70,727  median=$49,294  std=$76,117', WHITE, None, None),
        ("│ 2. Skewness: 3.72  →  strongly right-skewed distribution", WHITE, None, None),
        ("│ 3. Transformation: log transform recommended to normalise income", WHITE, None, None),
        ("│ 4. Mean > median by $21,432 — confirms right tail pulls average up", WHITE, None, None),
        ("│ 5. Outliers: max=$856,807 vs q3=$83,357 — extreme upper tail", WHITE, None, None),
        ("└───────────────────────────────────────────────────────────────────────┘", DIM, None, None),
        ("", None, "", None),
        ("Score: Correctness=1.0  Code Quality=0.50  Efficiency=1.0  Stat=1.0", YELLOW, None, None),
        ("       RDAB Score = 0.900 ✓", GREEN, None, None),
    ]

    img, d, y0 = terminal_canvas(len(lines) + 1, width=900)
    d.text((PAD, y0 - LINE - 2), "agent trace — eda_001 (gpt-4o)", fill=GREY, font=FONT_SM)
    y = y0

    for parts in lines:
        if parts[1] is None:
            y += LINE // 2
            continue
        x = PAD
        if parts[0]:
            d.text((x, y), parts[0], fill=parts[1], font=FONT_B)
            x += FONT_B.getlength(parts[0]) if hasattr(FONT_B, 'getlength') else len(parts[0]) * 8
        if parts[2]:
            col = parts[3] if parts[3] else WHITE
            d.text((x, y), parts[2], fill=col, font=FONT)
        y += LINE

    save(img, "agent_trace.png")


# ── 3. Terminal run ───────────────────────────────────────────────────────────
def make_terminal_run():
    lines = [
        ("$ ", GREEN, "dab run eda_001 --model gpt-4o", WHITE),
        ("", None, None, None),
        ("  Running eda_001  (model=gpt-4o, dry_run=False)", GREY, None, None),
        ("  Loading dataset …", GREY, None, None),
        ("  Starting agent loop …", GREY, None, None),
        ("  [step 1/4] get_dataframe_info       ✓", DIM, None, None),
        ("  [step 2/4] get_column_stats(income)  ✓", DIM, None, None),
        ("  [step 3/4] final answer              ✓", DIM, None, None),
        ("", None, None, None),
        ("  Complete.", GREEN, None, None),
        ("  Steps: 4  |  Tokens in: 990  out: 313  |  Cost: $0.052", CYAN, None, None),
        ("  Output saved → outputs/eda_001_20260409T094920.json", GREY, None, None),
        ("", None, None, None),
        ("$ ", GREEN, "dab score outputs/eda_001_20260409T094920.json", WHITE),
        ("", None, None, None),
        ("               ScoreCard — eda_001               ", CYAN, None, None),
        ("┏━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓", DIM, None, None),
        ("┃ Dimension     ┃ Score ┃ Weight ┃ Contribution ┃", WHITE, None, None),
        ("┡━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩", DIM, None, None),
        ("│ Correctness   │ 1.000 │   0.50 │        0.500 │", GREEN, None, None),
        ("│ Code Quality  │ 0.500 │   0.20 │        0.100 │", YELLOW, None, None),
        ("│ Efficiency    │ 1.000 │   0.15 │        0.150 │", GREEN, None, None),
        ("│ Stat Validity │ 1.000 │   0.15 │        0.150 │", GREEN, None, None),
        ("├───────────────┼───────┼────────┼──────────────┤", DIM, None, None),
        ("│ RDAB Score    │ 0.900 │   1.00 │        0.900 │", PURPLE, None, None),
        ("└───────────────┴───────┴────────┴──────────────┘", DIM, None, None),
        ("", None, None, None),
        ("$ ", GREEN, "dab models", WHITE),
        ("  claude-sonnet-4-6  ✓ ANTHROPIC_API_KEY set", GREEN, None, None),
        ("  gpt-4o             ✓ OPENAI_API_KEY set", GREEN, None, None),
        ("  gpt-4o-mini        ✓ OPENAI_API_KEY set", GREEN, None, None),
        ("  claude-haiku       ✓ ANTHROPIC_API_KEY set", GREEN, None, None),
        ("$ ", GREEN, "█", GREY),
    ]

    img, d, y0 = terminal_canvas(len(lines) + 1, width=860)
    d.text((300, 8), "terminal — dab run + score", fill=GREY, font=FONT_SM)
    y = y0

    for parts in lines:
        if parts[1] is None:
            y += LINE // 2
            continue
        x = PAD
        if parts[0]:
            d.text((x, y), parts[0], fill=parts[1], font=FONT_B)
            try:
                x += int(FONT_B.getlength(parts[0]))
            except:
                x += len(parts[0]) * 8
        if parts[2]:
            col = parts[3] if parts[3] else WHITE
            d.text((x, y), parts[2], fill=col, font=FONT)
        y += LINE

    save(img, "terminal_run.png")


# ── 4. Project structure ──────────────────────────────────────────────────────
def make_project_structure():
    tree = [
        ("RealDataAgentBench/", CYAN, True),
        ("├── realdataagentbench/", WHITE, True),
        ("│   ├── core/", BLUE, False),
        ("│   │   ├── task.py", GREY, False),
        ("│   │   └── registry.py", GREY, False),
        ("│   ├── datasets/", BLUE, False),
        ("│   │   └── generators/   # 23 seeded generators", GREEN, False),
        ("│   ├── harness/", BLUE, False),
        ("│   │   ├── agent.py      # multi-model agentic loop", GREY, False),
        ("│   │   ├── providers.py  # Claude · GPT-4o · GPT-4o-mini · Haiku", GREY, False),
        ("│   │   ├── tools.py      # run_code · get_dataframe_info · get_column_stats", GREY, False),
        ("│   │   └── tracer.py     # records every step + token count", GREY, False),
        ("│   └── scoring/", BLUE, False),
        ("│       ├── correctness.py", GREY, False),
        ("│       ├── code_quality.py", GREY, False),
        ("│       ├── efficiency.py", GREY, False),
        ("│       ├── stat_validity.py", GREY, False),
        ("│       └── composite.py  # weighted RDAB Score", GREY, False),
        ("├── tasks/", WHITE, True),
        ("│   ├── eda/                        # 3 tasks", YELLOW, False),
        ("│   ├── feature_engineering/        # 5 tasks", YELLOW, False),
        ("│   ├── modeling/                   # 5 tasks", YELLOW, False),
        ("│   ├── statistical_inference/      # 5 tasks", YELLOW, False),
        ("│   └── ml_engineering/             # 5 tasks", YELLOW, False),
        ("├── tests/                          # 150 offline tests", GREEN, False),
        ("├── outputs/                        # 44 benchmark run JSONs", GREY, False),
        ("├── scripts/", WHITE, False),
        ("│   └── build_leaderboard.py", GREY, False),
        ("├── docs/                           # GitHub Pages leaderboard", BLUE, False),
        ("│   ├── index.html", GREY, False),
        ("│   └── results.json", GREY, False),
        ("├── .github/workflows/              # CI: pytest + leaderboard rebuild", DIM, False),
        ("└── pyproject.toml", GREY, False),
    ]

    img, d, y0 = terminal_canvas(len(tree) + 3, width=880)
    d.text((300, 8), "project structure", fill=GREY, font=FONT_SM)
    y = y0
    d.text((PAD, y), "$ tree RealDataAgentBench/ -L 4", fill=GREEN, font=FONT_B)
    y += LINE
    d.text((PAD, y), "", fill=GREY, font=FONT)
    y += LINE // 2

    for (text, colour, bold) in tree:
        f = FONT_B if bold else FONT
        d.text((PAD, y), text, fill=colour, font=f)
        y += LINE

    y += 4
    d.text((PAD, y), "150 tests · 23 tasks · 44 runs · 4 models", fill=DIM, font=FONT_SM)

    save(img, "project_structure.png")


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating screenshots …")
    make_leaderboard()
    make_agent_trace()
    make_terminal_run()
    make_project_structure()
    print("Done.")
