# Knowledge base: cut WAM's website pages (pages.json) into small pieces ("chunks")
# and find the pieces that best match a visitor's message. No AI here, just Python.
import json
import math
import re

STOP_WORDS = set("""a an the of in on for to and or is are was were be been what which who how many much
when where why did does do with by from at as it its this that these those there their they you your
i me my we our us can could would should will about into than then so if not no yes please tell show
hi hello hey need want like get give have has any some also just know""".split())


PLACEHOLDER = re.compile(r"\b(lorem|ipsum|dolor|aliquam|vestibulum|curabitur|quisque|nullam|pellentesque|faucibus)\b", re.I)
NOISE = re.compile(r"^(see projects|show all|published by|admin|at|categories|related posts|read more|\d+|"
                   r"leave a reply.*|you must be logged in.*|sign in to receive|new projects|on your e-mail|"
                   r"email address:|leave this field empty.*|[a-z]+ \d{1,2}, \d{4})$", re.I)


def clean_text(text):
    """Remove what is not real information: theme placeholder text (lorem ipsum), blog tag lists,
    keyword-stuffed lines, newsletter form labels."""
    keep, in_tags = [], False
    for line in text.split("\n"):
        if line == "Tags":
            in_tags = True                  # a list of short blog tags follows, until a real sentence
            continue
        if in_tags and len(line) < 60:
            continue
        in_tags = False
        if PLACEHOLDER.search(line) or NOISE.match(line):
            continue
        parts = line.split(",")
        if len(parts) >= 8 and sum(len(p) for p in parts) / len(parts) < 40:
            continue                        # a long comma list of search keywords, written for Google
        keep.append(line)
    return "\n".join(keep)


def load_chunks(path="pages.json", size=120, step=90):
    """Return a list of {"title", "url", "text"} pieces of about `size` words."""
    chunks = []
    for page in json.load(open(path, encoding="utf-8")):
        words = clean_text(page["text"]).split()
        if len(words) < 15:
            continue                        # e.g. the contact page showed a 'Bot Verification' screen
        page["title"] = page["title"].split(" - ")[0].strip()
        for start in range(0, max(len(words) - 20, 1), step):
            text = " ".join(words[start:start + size])
            if len(text) > 60:
                chunks.append({"title": page["title"], "url": page["url"], "text": text})
    return chunks


def stem(word):
    """Very small 'stemmer' so services -> service, companies -> company."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]


def search(chunks, question, top=4):
    """Score every chunk by how many question words it (and its page title) contains; return the best ones."""
    q_words = set(tokens(question))
    all_words = [set(tokens(c["title"] + " " + c["text"])) for c in chunks]
    # rare words matter more: a word found in 1 chunk is a stronger clue than one found everywhere
    weight = {w: math.log((len(chunks) + 1) / (1 + sum(w in ws for ws in all_words))) + 1 for w in q_words}
    scored = []
    for chunk in chunks:
        c_words = tokens(chunk["text"])
        t_words = set(tokens(chunk["title"]))
        score = sum(min(c_words.count(w), 3) * weight[w] + (2 * weight[w] if w in t_words else 0) for w in q_words)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in scored[:top]]


if __name__ == "__main__":
    chunks = load_chunks()
    print("Chunks:", len(chunks))
    for q in ["Do you do WhatsApp marketing?", "How much is bulk SMS?", "Can you build an iPhone app?"]:
        best = search(chunks, q, top=1)
        print("\nQ:", q)
        print("Best match:", (best[0]["title"] + " | " + best[0]["text"][:200]) if best else "nothing found")
