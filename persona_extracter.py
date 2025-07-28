import os
import pdfplumber
import json
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Keywords to detect persona-relevant sentences
KEYWORDS = [
    "person", "individual", "traveller", "people", "he", "she", "they",
    "interested", "loves", "enjoys", "like", "dislike", "visit", "tourist",
    "visitor", "experience", "desire", "needs", "want", "prefer", "explore"
]

# Input/output folders
INPUT_FOLDER = "input_1B"
OUTPUT_FOLDER = "output_1b"

def extract_text_from_pdf(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text

def score_sentences(text):
    sentences = text.split('.')
    ranked = []
    for sent in sentences:
        lower = sent.lower()
        score = sum(1 for keyword in KEYWORDS if keyword in lower)
        if score > 0 and len(sent.strip()) > 20:
            ranked.append((score, sent.strip()))
    return sorted(ranked, reverse=True)

def summarize_text(text, sentence_count=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(sentence) for sentence in summary)

def process_pdf(file_path, file_name):
    print(f"Processing {file_name}...")
    raw_text = extract_text_from_pdf(file_path)
    ranked_sentences = score_sentences(raw_text)

    top_sentences = [s for _, s in ranked_sentences[:5]]
    summary = summarize_text(" ".join(top_sentences))

    return {
        "file": file_name,
        "top_sentences": top_sentences,
        "summary": summary
    }

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    for file_name in os.listdir(INPUT_FOLDER):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(INPUT_FOLDER, file_name)
            result = process_pdf(file_path, file_name)

            out_path = os.path.join(OUTPUT_FOLDER, file_name.replace(".pdf", ".json"))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

    print("✅ All PDFs processed. Check output_1B folder.")

if __name__ == "__main__":
    main()
