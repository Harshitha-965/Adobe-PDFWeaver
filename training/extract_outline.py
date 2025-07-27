import os
import json
from collections import defaultdict, Counter
import pdfplumber
from heuristics import process_spans, build_outline

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"

def extract_pdf_structure(pdf_path):
    structure = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            chars = page.chars
            # Group chars by rounded top coordinate to form lines
            lines = defaultdict(list)
            for ch in chars:
                top_key = round(ch["top"], 1)  # tweak decimal places if needed
                lines[top_key].append(ch)

            for top_key in sorted(lines.keys()):
                line_chars = lines[top_key]
                # Sort chars left to right
                line_chars.sort(key=lambda c: c["x0"])

                # Combine text of all chars in line
                line_text = "".join(c["text"] for c in line_chars).strip()

                # Get most common font size and fontname in line
                sizes = [round(c["size"], 1) for c in line_chars]
                fonts = [c["fontname"] for c in line_chars]

                most_common_size = Counter(sizes).most_common(1)[0][0]
                most_common_font = Counter(fonts).most_common(1)[0][0]

                bbox = (
                    min(c["x0"] for c in line_chars),
                    min(c["top"] for c in line_chars),
                    max(c["x1"] for c in line_chars),
                    max(c["bottom"] for c in line_chars),
                )

                span = {
                    "text": line_text,
                    "size": most_common_size,
                    "fontname": most_common_font,
                    "flags": 0,  # pdfplumber doesn't provide flags, so 0
                    "bbox": bbox,
                    "page": page_num
                }
                structure.append(span)
    return structure

def save_output(file_name, data):
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    for file_name in os.listdir(INPUT_FOLDER):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_FOLDER, file_name)
            print(f"Processing: {file_name}")
            try:
                structure = extract_pdf_structure(pdf_path)
                processed = process_spans(structure)
                outline_json = build_outline(processed)
                save_output(file_name, outline_json)
                print(f"✅ Done: {file_name}")
            except Exception as e:
                print(f"❌ Failed: {file_name} with error: {e}")

if __name__ == "__main__":
    main()