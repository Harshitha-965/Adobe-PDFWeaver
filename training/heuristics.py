import re

def normalize_text_spacing(text):
    """
    Fix spaced-out letters by removing spaces between single letters,
    but keep spaces between words intact.
    Example:
      "F r o n t e n d   A s s i g n m e n t" -> "Frontend Assignment"
    """
    # Step 1: collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text).strip()

    # Pattern matches sequences of spaced single letters (2 or more letters separated by spaces)
    pattern = r'(?:\b(?:[A-Za-z]\s){2,}[A-Za-z]\b)'

    def replacer(match):
        # Remove spaces within the matched group
        return match.group(0).replace(" ", "")

    # Replace all spaced single-letter sequences with letters joined together
    return re.sub(pattern, replacer, text)

def process_spans(spans):
    if not spans:
        return []

    size_counts = {}
    for span in spans:
        size = round(span["size"], 1)
        size_counts[size] = size_counts.get(size, 0) + 1

    if not size_counts:
        return []

    body_font_size = max(size_counts, key=size_counts.get)

    # Sort spans by page and vertical position (top coordinate)
    spans.sort(key=lambda s: (s["page"], s["bbox"][1]))

    processed = []
    for i, span in enumerate(spans):
        size = round(span["size"], 1)
        font_name = span["fontname"].lower()
        is_bold = "bold" in font_name

        tag = "paragraph"  # default tag

        if i == 0 and size >= body_font_size + 2:
            tag = "title"
        elif size >= body_font_size + 2:
            tag = "h1"
        elif size >= body_font_size + 1.2:
            tag = "h2"
        elif is_bold and size >= body_font_size + 0.5:
            tag = "h3"

        # Only keep title and headings, discard paragraphs
        if tag in ("title", "h1", "h2", "h3"):
            processed.append({
                "text": normalize_text_spacing(span["text"]),
                "size": size,
                "fontname": span["fontname"],
                "bbox": span["bbox"],
                "page": span["page"],
                "tag": tag
            })

    return processed

def build_outline(processed_spans):
    title_texts = []
    outline = []
    title_done = False

    for span in processed_spans:
        tag = span["tag"]
        text = span["text"]

        if tag == "title" and not title_done:
            title_texts.append(text)
        else:
            if not title_done:
                title_done = True

            if tag in ("h1", "h2", "h3"):
                outline.append({
                    "level": tag.upper(),
                    "text": text,
                    "page": span["page"]
                })

    title = " ".join(title_texts)
    title = re.sub(r"\s+", " ", title).strip()

    return {
        "title": title,
        "outline": outline
    }