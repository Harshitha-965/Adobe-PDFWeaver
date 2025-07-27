import re

def normalize_text_spacing(text):
    text = re.sub(r'\s+', ' ', text).strip()
    pattern = r'(?:\b(?:[A-Za-z]\s){2,}[A-Za-z]\b)'

    def replacer(match):
        return match.group(0).replace(" ", "")

    return re.sub(pattern, replacer, text)

def process_spans(spans, page_width=595):  # default A4 width in points
    if not spans:
        return []

    size_counts = {}
    for span in spans:
        size = round(span["size"], 1)
        size_counts[size] = size_counts.get(size, 0) + 1

    if not size_counts:
        return []

    body_font_size = max(size_counts, key=size_counts.get)
    max_size = max(size_counts.keys())

    spans.sort(key=lambda s: (s["page"], s["bbox"][1]))

    processed = []
    bold_keywords = ["bold", "black", "heavy", "semibold", "demibold", "extrabold", "extrablack", "medium"]

    for i, span in enumerate(spans):
        size = round(span["size"], 1)
        font_name = span["fontname"].lower()
        is_bold = any(keyword in font_name for keyword in bold_keywords)
        tag = "paragraph"  # default

        bbox = span["bbox"]
        left, top, right, bottom = bbox
        width = right - left
        center_x = left + width / 2

        # Check horizontal center alignment tolerance
        center_tolerance = 50  # points, adjust as needed

        is_centered = abs(center_x - page_width / 2) < center_tolerance
        near_top_first_page = (span["page"] == 1 and top < 100)

        # Title if:
        # 1. Near top of first page
        # 2. Bold
        # 3. Center aligned horizontally
        # 4. Size close to max_size or can be smaller (relax size here)
        if near_top_first_page and is_bold and is_centered and size >= body_font_size:
            tag = "title"
        # Previous heuristic for multiline titles:
        elif i < 10 and is_bold and size >= max_size - 0.3 and len(span["text"].strip()) > 3:
            tag = "title"
        elif size >= body_font_size + 1.8:
            tag = "h1"
        elif size >= body_font_size + 1.2:
            tag = "h2"
        elif is_bold and size >= body_font_size + 0.5:
            tag = "h3"

        processed.append({
            "text": normalize_text_spacing(span["text"]),
            "size": size,
            "fontname": span["fontname"],
            "bbox": bbox,
            "page": span["page"],
            "tag": tag
        })

    return processed

def build_outline(processed_spans):
    title_lines = []
    outline = []

    previous_title_span = None
    collecting_title = True

    for i, span in enumerate(processed_spans):
        tag = span["tag"]
        text = span["text"]

        if tag == "title" and collecting_title:
            # If we already have a previous title span, check spacing and font match
            if previous_title_span:
                prev_y = previous_title_span["bbox"][1]
                curr_y = span["bbox"][1]
                same_font = previous_title_span["fontname"] == span["fontname"]
                size_diff = abs(previous_title_span["size"] - span["size"]) <= 0.2
                vertical_gap_ok = abs(prev_y - curr_y) <= 100

                if not (same_font and size_diff and vertical_gap_ok):
                    collecting_title = False
                    continue

            title_lines.append(text)
            previous_title_span = span

        elif tag in ("h1", "h2", "h3"):
            collecting_title = False
            outline.append({
                "level": tag.upper(),
                "text": text,
                "page": span["page"]
            })

    title = " ".join(title_lines)
    title = re.sub(r"\s+", " ", title).strip()

    return {
        "title": title,
        "outline": outline
    }
