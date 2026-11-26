import time
from retriever import retrieve
from llm import answer

# Write your own questions here.
# "keyword" is a word that must appear in a correct answer.
# "page" is the page of the PDF where the answer really is.
TESTS = [
    {"q": "Your first question here", "keyword": "expected word", "page": 1},
    {"q": "Your second question here", "keyword": "expected word", "page": 2},
]

answer_ok = 0
source_ok = 0
for i, t in enumerate(TESTS, 1):
    chunks = retrieve(t["q"])                 # find the closest chunks
    reply = answer(t["q"], chunks, [])        # ask Gemini with no chat history
    a = t["keyword"].lower() in reply.lower() # is the expected word in the answer?
    s = t["page"] in [c["page"] for c in chunks]  # was the right page retrieved?
    answer_ok += a
    source_ok += s
    print(i, "answer OK" if a else "answer WRONG", "| source OK" if s else "| source MISSING")
    time.sleep(4)                             # pause so the free API limit is not hit

n = len(TESTS)
print(f"Answers correct: {answer_ok}/{n}")
print(f"Source page correct: {source_ok}/{n}")