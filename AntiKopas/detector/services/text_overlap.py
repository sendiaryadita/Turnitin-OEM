import re


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_ngrams(text, n=5):
    words = normalize_text(text).split()

    if len(words) < n:
        return set(words)

    return {
        " ".join(words[i:i + n])
        for i in range(len(words) - n + 1)
    }


def calculate_text_overlap(text_a, text_b, n=5):
    grams_a = make_ngrams(text_a, n)
    grams_b = make_ngrams(text_b, n)

    if not grams_a or not grams_b:
        return 0.0

    intersection = grams_a.intersection(grams_b)

    overlap_score = len(intersection) / len(grams_a)

    return round(overlap_score, 4)