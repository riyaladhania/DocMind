
import os
import time
import json
from dotenv import load_dotenv
from groq import Groq


# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from .env")

gclient = Groq(api_key=api_key)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# Common function to call Groq
def ask_groq(prompt, max_tokens=1024):

    for attempt in range(3):
        try:
            response = gclient.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=max_tokens
            )

            result = response.choices[0].message.content

            if not result:
                raise RuntimeError("Groq returned an empty response.")

            return result.strip()

        except Exception as e:
            status_code = getattr(e, "status_code", None)

            if status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == 2:
                raise

            wait_time = 2 * (attempt + 1)

            print(
                f"Groq temporarily unavailable. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


# Prepare conversation history
def prepare_history(history):
    return "\n".join(
        f"{h['role']}: {h['content']}"
        for h in history[-8:]
    )


# DOCUMENT MODE
def answer(question, chunks, history):

    context = "\n\n".join(
        f"[Page {c['page']}] {c['text']}"
        for c in chunks
    )

    past = prepare_history(history)

    prompt = f"""
You are DocMind, an intelligent PDF assistant.

Your job is to answer questions using ONLY the PDF context.

IMPORTANT UNDERSTANDING RULES:

1. Understand English, Hindi and Hinglish.
2. Understand common short forms, abbreviations and informal typing.
3. Understand spelling mistakes and incomplete sentences when the meaning
   is clear.
4. Understand follow-up questions using previous conversation.
5. For words like "it", "this", "explain more", "iska matlab",
   identify the correct topic from conversation history.
6. Do not ask the user to repeat a question when its meaning is clear.
7. Give simple, clear and well-formatted explanations.
8. Answer in the language used by the user.

DOCUMENT RULES:

- Use ONLY the supplied PDF context for factual document answers.
- Never invent information or page numbers.
- Mention page numbers whenever possible.
- If the answer is not available in the PDF, reply exactly:
  "I couldn't find this in the document."
- Even if you know the answer from general knowledge, do not use it
  when it is missing from the PDF.

Previous conversation:
{past}

PDF context:
{context}

Current question:
{question}

Answer:
"""

    return ask_groq(prompt, 1200)


# GENERAL AI MODE
def answer_general(question, history):

    past = prepare_history(history)

    prompt = f"""
You are DocMind, a helpful general AI assistant.

Answer the user's question using your general knowledge.

UNDERSTANDING RULES:

1. Understand English, Hindi and Hinglish.
2. Understand short forms, abbreviations and informal typing.
3. Understand spelling mistakes and incomplete sentences.
4. Understand follow-up questions from previous messages.
5. Understand phrases such as "explain it", "iska matlab",
   "short me batao", "example do" and similar expressions.
6. Do not ask unnecessary clarification questions.
7. Give simple explanations with examples when useful.
8. Use headings, bullet points and numbered steps when appropriate.
9. Answer in the language used by the user.
10. Be friendly, accurate and helpful.

Previous conversation:
{past}

Current question:
{question}

Answer:
"""

    return ask_groq(prompt, 1200)


# Generate document-related and general suggestions
def suggest_question_groups(question, chunks, answer_text):

    context = "\n\n".join(
        f"[Page {c['page']}] {c['text']}"
        for c in chunks
    )

    prompt = f"""
You are DocMind's question suggestion assistant.

Generate useful questions based on the user's current question,
the PDF content and the answer.

Return exactly this JSON structure:

{{
  "document_questions": [
    "Question 1",
    "Question 2",
    "Question 3"
  ],
  "general_questions": [
    "Question 1",
    "Question 2",
    "Question 3"
  ]
}}

RULES:

DOCUMENT QUESTIONS:
- Must be answerable using the supplied PDF.
- Suggest useful related concepts, explanations or examples.
- Do not repeat the user's question.

GENERAL QUESTIONS:
- Must explore the same topic using general knowledge.
- Can ask for real-life examples, practical uses or deeper explanations.
- They do not need to be answerable from the PDF.
- Do not repeat document questions.

For both groups:
- Keep questions short and natural.
- Understand the user's language.
- Do not provide answers.
- Return valid JSON only.

PDF content:
{context}

User question:
{question}

Previous answer:
{answer_text}
"""

    result = ask_groq(prompt, 500)

    try:
        # Remove possible Markdown code fences
        cleaned = result.replace("```json", "").replace("```", "").strip()

        data = json.loads(cleaned)

        return {
            "document_questions": data.get("document_questions", [])[:3],
            "general_questions": data.get("general_questions", [])[:3]
        }

    except (json.JSONDecodeError, AttributeError):
        print("Could not parse suggested questions.")
        return {
            "document_questions": [],
            "general_questions": []
        }


# Backward-compatible function for the existing main.py
def suggest_questions(question, chunks, answer_text):

    groups = suggest_question_groups(
        question,
        chunks,
        answer_text
    )

    return groups["document_questions"]
