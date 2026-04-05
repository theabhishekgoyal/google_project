"""
Generate the architecture pipeline diagram as a PNG image.
Uses Pillow (PIL) — no extra dependencies needed.
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "pipeline_diagram.png")

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1200, 900
BG = "#FFFFFF"
BOX_FILL = "#E3F2FD"
BOX_STROKE = "#1565C0"
ARROW_COLOR = "#1565C0"
HIGHLIGHT_FILL = "#FFF3E0"
HIGHLIGHT_STROKE = "#E65100"
DECISION_FILL = "#E8F5E9"
DECISION_STROKE = "#2E7D32"
TEXT_COLOR = "#212121"
SUBTEXT_COLOR = "#616161"

def draw_diagram():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Try to load a nice font, fall back to default
    try:
        font_b = ImageFont.truetype("arialbd.ttf", 18)
        font = ImageFont.truetype("arial.ttf", 15)
        font_s = ImageFont.truetype("arial.ttf", 13)
    except (OSError, IOError):
        try:
            font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            font = ImageFont.truetype("DejaVuSans.ttf", 15)
            font_s = ImageFont.truetype("DejaVuSans.ttf", 13)
        except (OSError, IOError):
            font_b = ImageFont.load_default()
            font = ImageFont.load_default()
            font_s = ImageFont.load_default()

    def draw_box(x, y, w, h, text, subtext=None, fill=BOX_FILL, stroke=BOX_STROKE, radius=12):
        d.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=stroke, width=2)
        if subtext:
            d.text((x + w//2, y + h//2 - 12), text, fill=TEXT_COLOR, font=font_b, anchor="mm")
            d.text((x + w//2, y + h//2 + 12), subtext, fill=SUBTEXT_COLOR, font=font_s, anchor="mm")
        else:
            d.text((x + w//2, y + h//2), text, fill=TEXT_COLOR, font=font_b, anchor="mm")

    def arrow_down(x, y1, y2):
        d.line([(x, y1), (x, y2)], fill=ARROW_COLOR, width=3)
        d.polygon([(x-7, y2-10), (x+7, y2-10), (x, y2)], fill=ARROW_COLOR)

    def arrow_down_split(x, y1, x_left, x_right, y2):
        mid_y = (y1 + y2) // 2
        d.line([(x, y1), (x, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x, mid_y), (x_left, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x, mid_y), (x_right, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x_left, mid_y), (x_left, y2)], fill=ARROW_COLOR, width=3)
        d.line([(x_right, mid_y), (x_right, y2)], fill=ARROW_COLOR, width=3)
        d.polygon([(x_left-7, y2-10), (x_left+7, y2-10), (x_left, y2)], fill=ARROW_COLOR)
        d.polygon([(x_right-7, y2-10), (x_right+7, y2-10), (x_right, y2)], fill=ARROW_COLOR)

    def arrow_merge(x_left, x_right, y1, x_center, y2):
        mid_y = (y1 + y2) // 2
        d.line([(x_left, y1), (x_left, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x_right, y1), (x_right, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x_left, mid_y), (x_right, mid_y)], fill=ARROW_COLOR, width=3)
        d.line([(x_center, mid_y), (x_center, y2)], fill=ARROW_COLOR, width=3)
        d.polygon([(x_center-7, y2-10), (x_center+7, y2-10), (x_center, y2)], fill=ARROW_COLOR)

    cx = W // 2  # center x

    # Row 1: User Upload
    bw, bh = 400, 50
    y = 20
    draw_box(cx - bw//2, y, bw, bh, "User Uploads Policy PDF + Hospital Bill")

    # Arrow down split
    y1_arrow = y + bh
    y2_arrow = y + bh + 55
    left_cx = cx - 200
    right_cx = cx + 200
    arrow_down_split(cx, y1_arrow, left_cx, right_cx, y2_arrow)

    # Row 2: Document Processing (two boxes)
    bw2 = 340
    bh2 = 55
    y2 = y2_arrow
    draw_box(left_cx - bw2//2, y2, bw2, bh2,
             "Document Processing + Bill Parser",
             "Gemini Vision API | OCR + Regex fallback",
             fill=HIGHLIGHT_FILL, stroke=HIGHLIGHT_STROKE)
    draw_box(right_cx - bw2//2, y2, bw2, bh2,
             "Policy Chunker",
             "PyMuPDF | ~500-char segments + page metadata")

    # Arrow from right box down to TF-IDF
    y3_start = y2 + bh2
    y3_end = y3_start + 55
    arrow_down(right_cx, y3_start, y3_end)

    # Row 3: TF-IDF Retriever (right side)
    bw3 = 340
    bh3 = 55
    y3 = y3_end
    draw_box(right_cx - bw3//2, y3, bw3, bh3,
             "TF-IDF Clause Retriever",
             "Bigrams (5000 features) + Cosine Similarity")

    # Merge arrows from Bill Parser and TF-IDF into Rule Engine
    y4_start_left = y2 + bh2
    y4_start_right = y3 + bh3
    # Draw left arrow going straight down to merge level
    merge_y = y4_start_right + 30
    y4_end = merge_y + 30
    # left side goes down
    d.line([(left_cx, y4_start_left), (left_cx, merge_y)], fill=ARROW_COLOR, width=3)
    # right side goes down
    d.line([(right_cx, y4_start_right), (right_cx, merge_y)], fill=ARROW_COLOR, width=3)
    # horizontal merge
    d.line([(left_cx, merge_y), (right_cx, merge_y)], fill=ARROW_COLOR, width=3)
    # center down
    d.line([(cx, merge_y), (cx, y4_end)], fill=ARROW_COLOR, width=3)
    d.polygon([(cx-7, y4_end-10), (cx+7, y4_end-10), (cx, y4_end)], fill=ARROW_COLOR)

    # Row 4: Rule Engine
    bw4 = 440
    bh4 = 55
    y4 = y4_end
    draw_box(cx - bw4//2, y4, bw4, bh4,
             "Rule Engine (10 YAML-Configured Rules)",
             "Waiting Period | Room Rent | Exclusions | Pre-Existing | Co-Pay ...")

    # Arrow down
    arrow_down(cx, y4 + bh4, y4 + bh4 + 45)

    # Row 5: Line-Item Reconciliation
    bw5 = 440
    bh5 = 50
    y5 = y4 + bh4 + 45
    draw_box(cx - bw5//2, y5, bw5, bh5,
             "Line-Item Reconciliation",
             "Each bill item matched to policy: Covered | Excluded | Sub-Limited")

    # Arrow down
    arrow_down(cx, y5 + bh5, y5 + bh5 + 45)

    # Row 6: Decision Builder
    bw6 = 440
    bh6 = 55
    y6 = y5 + bh5 + 45
    draw_box(cx - bw6//2, y6, bw6, bh6,
             "Decision Builder",
             "APPROVE / REJECT / PARTIAL + Audit Record (JSON)",
             fill=DECISION_FILL, stroke=DECISION_STROKE)

    # Arrow down
    arrow_down(cx, y6 + bh6, y6 + bh6 + 45)

    # Row 7: UI
    bw7 = 440
    bh7 = 50
    y7 = y6 + bh6 + 45
    draw_box(cx - bw7//2, y7, bw7, bh7,
             "Streamlit UI + FastAPI REST API",
             "Interactive results | Rule audit trail | Policy citations")

    # Title at top-right corner
    d.text((W - 20, H - 20), "Insurance Claim Settlement Agent — Pipeline", fill=SUBTEXT_COLOR, font=font_s, anchor="rb")

    img.save(OUTPUT, "PNG", dpi=(200, 200))
    print(f"Diagram saved: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    draw_diagram()
