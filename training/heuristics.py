import re

def normalize_text_spacing(text):
    text = re.sub(r'\s+', ' ', text).strip()
    pattern = r'(?:\b(?:[A-Za-z]\s){2,}[A-Za-z]\b)'

    def replacer(match):
        return match.group(0).replace(" ", "")

    return re.sub(pattern, replacer, text)

def process_spans(spans, page_width=595):
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
        text = span["text"].strip()
        if not text:
            continue

        size = round(span["size"], 1)
        font_name = span["fontname"].lower()
        is_bold = any(keyword in font_name for keyword in bold_keywords)
        tag = "paragraph"

        bbox = span["bbox"]
        left, top, right, bottom = bbox
        width = right - left
        center_x = left + width / 2

        center_tolerance = 50
        is_centered = abs(center_x - page_width / 2) < center_tolerance
        near_top_first_page = (span["page"] == 1 and top < 200)

        if near_top_first_page and is_bold and is_centered and size >= body_font_size:
            tag = "title"
        elif i < 15 and is_bold and size >= max_size - 0.3 and len(text) > 3:
            tag = "title"
        elif size >= body_font_size + 1.5:
            tag = "h1"
        elif size >= body_font_size + 1.2:
            tag = "h2"
        elif is_bold and size >= body_font_size + 0.5:
            tag = "h3"

        processed.append({
            "text": normalize_text_spacing(text),
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
    title_fontname = None
    title_fontsize = None
    title_page = 1

    for i, span in enumerate(processed_spans):
        tag = span["tag"]
        text = span["text"]
        page = span["page"]

        if collecting_title and tag == "title":
            if previous_title_span:
                prev_y = previous_title_span["bbox"][1]
                curr_y = span["bbox"][1]
                vertical_gap = abs(curr_y - prev_y)

                same_font = previous_title_span["fontname"] == span["fontname"]
                size_diff = abs(previous_title_span["size"] - span["size"]) <= 0.3
                gap_ok = vertical_gap <= 110

                if same_font and size_diff and gap_ok and page == title_page:
                    title_lines.append(text)
                    previous_title_span = span
                else:
                    collecting_title = False
                    continue
            else:
                title_lines.append(text)
                previous_title_span = span
                title_fontname = span["fontname"]
                title_fontsize = span["size"]
                title_page = page
        elif tag in ("h1", "h2", "h3"):
            if collecting_title:
                # Avoid treating paragraph directly under a multi-line title as heading
                if previous_title_span:
                    prev_bottom = previous_title_span["bbox"][3]
                    curr_top = span["bbox"][1]
                    if span["page"] == title_page and 0 < curr_top - prev_bottom < 50:
                        continue
                collecting_title = False

            outline.append({
                "level": tag.upper(),
                "text": text,
                "page": page
            })

    title = " ".join(title_lines)
    title = re.sub(r"\s+", " ", title).strip()

    return {
        "title": title,
        "outline": outline
    }
