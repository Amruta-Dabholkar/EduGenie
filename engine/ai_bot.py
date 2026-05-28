import json
import re
from groq import Groq

GROQ_API_KEY = "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"
MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

def _call_groq(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI ERROR] Groq call failed: {e}")
        return ""

def generate_notes(text):
    prompt = f"""Generate study notes as JSON with exactly these keys:
- summary (string, 3-4 sentences)
- key_points (list of 5 strings)
- key_definitions (list of objects with 'term' and 'definition')
Return ONLY valid JSON, no markdown, no code fences.
Content: {text[:5000]}"""
    raw = _call_groq(prompt).replace("```json","").replace("```","").strip()
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return {"summary": "Could not generate notes.", "key_points": [], "key_definitions": []}

def generate_quiz(text, num_questions=5):
    prompt = f"""Generate {num_questions} MCQs as a JSON array.
Each item must have: question, options (A/B/C/D), answer.
Return ONLY valid JSON array, no markdown, no code fences.
Content: {text[:5000]}"""
    raw = _call_groq(prompt).replace("```json","").replace("```","").strip()
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return [{"question": "Could not generate quiz.", "options": {}, "answer": ""}]

def answer_doubt(context_text, question):
    if context_text:
        prompt = f"Answer this student question: {question}\n\nBased on this content: {context_text[:5000]}"
    else:
        prompt = f"Answer this question clearly: {question}"
    answer = _call_groq(prompt)
    return answer if answer else "Sorry, could not generate answer."

#**Step 4:** Press `Ctrl+S`, restart:
#C:/Users/lenovo/AppData/Local/Programs/Python/Python310/python.exe app.py