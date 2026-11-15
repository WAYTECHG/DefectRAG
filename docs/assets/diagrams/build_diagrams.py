"""Build the README architecture diagrams as light and dark SVGs.

    python docs/assets/diagrams/build_diagrams.py

Writes architecture-{light,dark}.svg and pipelines-{light,dark}.svg next to this file.
Edit the boxes here, not the SVG output.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent
FONT = "Segoe UI,Inter,-apple-system,Helvetica,Arial,sans-serif"
MONO = "Cascadia Code,Consolas,SFMono-Regular,Menlo,monospace"

ACCENTS = {
    "client": "#2563eb",
    "serving": "#7c3aed",
    "vision": "#0891b2",
    "assistant": "#d97706",
    "data": "#16a34a",
    "ops": "#64748b",
    "stop": "#dc2626",
}
THEMES = {
    "light": {
        "bg": "#ffffff",
        "border": "#e5e7eb",
        "text": "#0f172a",
        "muted": "#475569",
        "box": "#ffffff",
        "tint": 0.07,
        "line": "#94a3b8",
        "chip": "#f1f5f9",
    },
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "text": "#e6edf3",
        "muted": "#9da7b3",
        "box": "#161b22",
        "tint": 0.13,
        "line": "#6e7681",
        "chip": "#21262d",
    },
}


class Canvas:
    def __init__(self, width, height, theme, title, desc):
        self.w, self.h, self.t = width, height, THEMES[theme]
        self.parts = []
        self.title, self.desc = title, desc

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=13, weight=400, color=None, anchor="middle", family=FONT, spacing=0):
        color = color or self.t["text"]
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.add(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}"{ls}>{escape(s)}</text>'
        )

    def group(self, x, y, w, h, kind, label, note=""):
        c = ACCENTS[kind]
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{c}" fill-opacity="{self.t["tint"]}" '
            f'stroke="{c}" stroke-opacity="0.55" stroke-width="1.2"/>'
        )
        self.add(f'<rect x="{x + 16}" y="{y + 14}" width="6" height="18" rx="3" fill="{c}"/>')
        self.text(x + 30, y + 28, label, 12.5, 700, c, "start", spacing=1.2)
        if note:
            self.text(x + w - 16, y + 28, note, 11.5, 400, self.t["muted"], "end")

    def box(self, x, y, w, h, kind, title, lines=(), mono_first=False):
        c = ACCENTS[kind]
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{self.t["box"]}" stroke="{c}" '
            f'stroke-opacity="0.8" stroke-width="1.3"/>'
        )
        self.add(f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{c}"/>')
        total = 18 + 16 * len(lines)
        top = y + (h - total) / 2 + 13
        self.text(x + w / 2 + 2, top, title, 12.5 if mono_first else 13.5, 650, family=MONO if mono_first else FONT)
        for i, line in enumerate(lines):
            self.text(x + w / 2 + 2, top + 19 + 16 * i, line, 11.5, 400, self.t["muted"])

    def arrow(self, points, color=None, label="", lx=None, ly=None, dashed=False, marker="arr"):
        color = color or self.t["line"]
        d = "M" + " L".join(f"{px},{py}" for px, py in points)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self.add(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} '
            f'marker-end="url(#{marker})" stroke-linejoin="round"/>'
        )
        if label:
            self.chip(lx, ly, label, color if dashed else None)

    def chip(self, x, y, s, color=None):
        width = 7 + 6.1 * len(s)
        self.add(
            f'<rect x="{x - width / 2}" y="{y - 11}" width="{width}" height="17" rx="8.5" fill="{self.t["chip"]}" '
            f'stroke="{self.t["border"]}"/>'
        )
        self.text(x, y + 2, s, 10.5, 500, color or self.t["muted"])

    def svg(self):
        t = self.t
        markers = "".join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            for mid, col in (("arr", t["line"]), ("stop", ACCENTS["stop"]), ("ok", ACCENTS["data"]))
        )
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
            f'height="{self.h}" role="img" aria-labelledby="t d"><title id="t">{escape(self.title)}</title>'
            f'<desc id="d">{escape(self.desc)}</desc><defs>{markers}</defs>'
            f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="18" fill="{t["bg"]}" '
            f'stroke="{t["border"]}"/>'
        )
        return head + "".join(self.parts) + "</svg>\n"


def architecture(theme):
    c = Canvas(
        1200,
        960,
        theme,
        "DefectRAG system architecture",
        "React dashboard calls a Hugging Face Space that runs the DINOv2 detector and the LangGraph evidence "
        "assistant on ZeroGPU; Supabase stores accounts, inspections and cases; n8n on AWS sends case emails.",
    )
    c.text(40, 48, "DefectRAG · System architecture", 22, 700, anchor="start")
    c.text(
        40,
        72,
        "One dashboard, two AI pipelines, one shared data layer. Arrows show the direction of each request.",
        13,
        400,
        c.t["muted"],
        "start",
    )

    # Client
    c.group(30, 100, 230, 500, "client", "CLIENT", "browser")
    for i, (title, lines) in enumerate(
        [
            ("React 19 + Vite", ["dashboard, light/dark"]),
            ("Upload & inspect", ["photo + product"]),
            ("Heatmap & compare", ["score, verdict, limit"]),
            ("Ask the assistant", ["cited answers"]),
            ("supabase-js", ["auth, history, cases"]),
        ]
    ):
        c.box(48, 148 + 86 * i, 194, 66, "client", title, lines, mono_first=title == "supabase-js")

    # Serving
    c.group(300, 100, 230, 500, "serving", "SERVING", "HF Space")
    c.box(318, 148, 194, 80, "serving", "Gradio 6.30 + FastAPI", ["server mode, REST", "upload + file checks"])
    c.box(318, 262, 194, 80, "serving", "ZeroGPU queue", ["@spaces.GPU jobs", "DINOv2 + Qwen on GPU"])
    c.box(318, 376, 194, 66, "serving", "CPU worker", ["BGE embeddings"])
    c.box(318, 476, 194, 80, "serving", "Local mode", ["Uvicorn + Ollama", "SQLite, offline"])

    # Vision
    c.group(560, 100, 610, 240, "vision", "VISION PIPELINE", "fine-tuned DINOv2 + coreset memory")
    vx = [578 + 148 * i for i in range(4)]
    for x, (title, lines) in zip(
        vx,
        [
            ("Preprocess", ["448 px short edge", "PCA foreground mask"]),
            ("DINOv2 ViT-S/14", ["14 px patches", "last 4 blocks tuned"]),
            ("Patch memory", ["32,768 per product", "farthest-point set"]),
            ("Score + heatmap", ["nearest-patch gap", "95th-pct limit"]),
        ],
    ):
        c.box(x, 150, 128, 104, "vision", title, lines)
    for x in vx[:-1]:
        c.arrow([(x + 128, 202), (x + 148, 202)])
    c.text(
        865, 290, "VisA image AUROC 0.950 → 0.971  ·  MVTec AD 0.992 with no MVTec training", 12, 600, ACCENTS["vision"]
    )
    c.text(865, 312, "Verdict: normal  ·  closer look (within 5% of the limit)  ·  unusual", 11.5, 400, c.t["muted"])

    # Assistant
    c.group(560, 360, 610, 240, "assistant", "EVIDENCE ASSISTANT", "LangGraph state machine")
    ax = [578 + 148 * i for i in range(4)]
    for x, (title, lines) in zip(
        ax,
        [
            ("Scope check", ["route node", "out of scope: abstain"]),
            ("BGE retrieval", ["top-3, sim ≥ 0.50", "source filter"]),
            ("Qwen2.5-3B", ["QLoRA fine-tuned", "JSON-schema output"]),
            ("Answer checks", ["exact-quote match", "citation + numbers"]),
        ],
    ):
        c.box(x, 410, 128, 104, "assistant", title, lines)
    for x in ax[:-1]:
        c.arrow([(x + 128, 462), (x + 148, 462)])
    c.text(
        865,
        550,
        "Grounded answers 42% → 89% after fine-tuning  ·  0 of 20 wrong answers on unanswerable",
        12,
        600,
        ACCENTS["assistant"],
    )
    c.text(
        865,
        572,
        "Questions about the saved score skip the LLM and read the stored measurement",
        11.5,
        400,
        c.t["muted"],
    )

    # Client -> serving, serving -> pipelines
    c.arrow([(242, 214), (318, 214)], label="HTTPS", lx=280, ly=202)
    c.arrow([(512, 302), (540, 302), (540, 202), (578, 202)], label="GPU jobs", lx=540, ly=332)
    c.arrow([(540, 302), (540, 462), (578, 462)])

    # Data
    c.group(30, 630, 1140, 160, "data", "DATA & AUTOMATION", "Supabase + n8n on AWS")
    dx = [48 + 188 * i for i in range(6)]
    for x, (title, lines) in zip(
        dx,
        [
            ("Supabase Auth", ["email confirm", "TOTP MFA for staff"]),
            ("Storage", ["inspection photos", "and heatmaps"]),
            ("Postgres + RLS", ["inspections, reviews", "corrective actions"]),
            ("Event queue", ["one-effect ledger", "Edge Function lease"]),
            ("n8n on AWS", ["Lightsail workflow", "deadlines, reminders"]),
            ("Email via Resend", ["supervisor + owner", "retry, never blocks"]),
        ],
    ):
        c.box(x, 678, 164, 90, "data", title, lines)
    for x in dx[2:-1]:
        c.arrow([(x + 164, 723), (x + 186, 723)])
    c.arrow([(145, 600), (145, 678)], label="auth + data (RLS)", lx=145, ly=617)
    c.arrow([(415, 600), (415, 614), (318, 614), (318, 678)], label="results", lx=366, ly=614)

    # Ops
    c.group(30, 820, 1140, 116, "ops", "DELIVERY & OPERATIONS")
    ox = [48 + 376 * i for i in range(3)]
    for x, (title, lines) in zip(
        ox,
        [
            ("GitHub Actions CI", ["ruff · mypy · pytest · 510 tests"]),
            ("One-click release", ["approved deploy to the HF Space"]),
            ("AWS monitoring", ["Lightsail showcase · Lambda · CloudWatch"]),
        ],
    ):
        c.box(x, 864, 352, 56, "ops", title, lines)
    c.arrow([(400, 892), (424, 892)])
    return c.svg()


def pipelines(theme):
    c = Canvas(
        1200,
        760,
        theme,
        "DefectRAG inspection and question pipelines",
        "Step by step: how a photo becomes a heatmap and verdict, and how a question becomes a cited answer "
        "or an abstention in the LangGraph workflow.",
    )
    c.text(40, 48, "DefectRAG · Request pipelines", 22, 700, anchor="start")
    c.text(
        40,
        72,
        "What happens to one photo and one question. Code names match backend/highres.py and backend/rag.py.",
        13,
        400,
        c.t["muted"],
        "start",
    )

    # 1. Inspection
    c.group(30, 100, 1140, 230, "vision", "1 · INSPECT A PHOTO", "backend/highres.py")
    xs = [48 + 186 * i for i in range(6)]
    steps = [
        ("Photo", ["any size, any product", "upload checks"]),
        ("Resize", ["short edge 448 px", "3:2 → 32 × 48 patches"]),
        ("DINOv2 encoder", ["1,536 patch vectors", "fine-tuned on VisA"]),
        ("Foreground mask", ["PCA on patch features", "ignores background"]),
        ("Nearest neighbour", ["each patch vs memory", "32,768 normal patches"]),
        ("Score + verdict", ["heatmap = patch gaps", "score vs product limit"]),
    ]
    for x, (title, lines) in zip(xs, steps):
        c.box(x, 150, 162, 96, "vision", title, lines)
    for x in xs[:-1]:
        c.arrow([(x + 162, 198), (x + 184, 198)])
    verdicts = [("normal", ACCENTS["data"]), ("closer look", ACCENTS["assistant"]), ("unusual", ACCENTS["stop"])]
    px = 760
    c.text(px - 12, 290, "Result:", 12, 600, anchor="end")
    for name, col in verdicts:
        w = 18 + 7 * len(name)
        c.add(
            f'<rect x="{px}" y="{276}" width="{w}" height="21" rx="10.5" fill="{col}" fill-opacity="0.15" '
            f'stroke="{col}"/>'
        )
        c.text(px + w / 2, 291, name, 11.5, 600, col)
        px += w + 10
    c.text(
        48,
        290,
        "The limit is the 95th percentile of held-out normal scores; nothing defective is used to set it.",
        11.5,
        400,
        c.t["muted"],
        "start",
    )
    c.text(
        48,
        310,
        "Closer look = within 5% of the limit, so borderline photos go to a person.",
        11.5,
        400,
        c.t["muted"],
        "start",
    )

    # 2. Question
    c.group(30, 360, 1140, 370, "assistant", "2 · ASK A QUESTION", "LangGraph StateGraph · backend/rag.py")
    c.box(48, 420, 140, 70, "client", "Question", ["+ linked inspection"])
    c.box(224, 420, 150, 70, "assistant", "Measurement?", ["score, limit, verdict"])
    c.box(224, 560, 150, 70, "data", "Saved facts", ["no LLM, exact values"])
    nodes = [
        (410, "route", ["scope check"]),
        (560, "retrieve", ["BGE top-3 ≥ 0.50"]),
        (710, "validate_evidence", ["source, licence"]),
        (860, "generate", ["Qwen2.5-3B QLoRA"]),
        (1010, "validate_answer", ["quote, numbers"]),
    ]
    for x, name, lines in nodes:
        c.box(x, 420, 140 if x != 1010 else 142, 70, "assistant", name, lines, mono_first=True)
    c.arrow([(188, 455), (224, 455)])
    c.arrow([(374, 455), (410, 455)], label="no", lx=392, ly=443)
    c.arrow([(299, 490), (299, 560)], label="yes", lx=299, ly=525)
    for (x, *_), (nx, *_) in zip(nodes, nodes[1:]):
        c.arrow([(x + 140, 455), (nx, 455)])

    # Abstain + outcomes
    stop = ACCENTS["stop"]
    c.add(
        f'<rect x="560" y="575" width="290" height="62" rx="9" fill="{stop}" fill-opacity="0.10" stroke="{stop}" '
        f'stroke-width="1.3"/>'
    )
    c.text(705, 600, "abstain", 13.5, 650, stop, family=MONO)
    c.text(705, 620, "“The documentation does not establish that claim.”", 11.5, 400, c.t["muted"])
    c.arrow(
        [(480, 490), (480, 606), (560, 606)], stop, "root cause, repair, count…", 480, 545, dashed=True, marker="stop"
    )
    c.arrow([(780, 490), (780, 575)], stop, "no evidence left", 780, 532, dashed=True, marker="stop")

    ok = ACCENTS["data"]
    c.add(
        f'<rect x="910" y="575" width="242" height="62" rx="9" fill="{ok}" fill-opacity="0.10" stroke="{ok}" '
        f'stroke-width="1.3"/>'
    )
    c.text(1031, 600, "Cited answer", 13.5, 650, ok)
    c.text(1031, 620, "claim + exact quote + source link", 11.5, 400, c.t["muted"])
    c.arrow([(1081, 490), (1081, 575)], ok, "passes", 1081, 532, marker="ok")
    c.text(1031, 662, "If no claim passes: show the retrieved", 11, 400, c.t["muted"])
    c.text(1031, 677, "sentences only (retrieval-only mode)", 11, 400, c.t["muted"])
    c.text(
        48,
        700,
        "The model only picks which retrieved sentence answers the question and restates it; code checks that",
        11.5,
        400,
        c.t["muted"],
        "start",
    )
    c.text(
        48,
        717,
        "the quote exists word for word in the source and that every number in the answer appears in that quote.",
        11.5,
        400,
        c.t["muted"],
        "start",
    )
    return c.svg()


if __name__ == "__main__":
    for theme in THEMES:
        (OUT / f"architecture-{theme}.svg").write_text(architecture(theme), encoding="utf-8")
        (OUT / f"pipelines-{theme}.svg").write_text(pipelines(theme), encoding="utf-8")
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
