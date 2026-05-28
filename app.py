
import os
from flask import Flask, render_template, request, jsonify, session
from engine.db import get_user, register_user, save_score, get_scores
from engine.pdf_parser import extract_text_from_pdf
from engine.ai_bot import generate_quiz, generate_notes, answer_doubt
from dotenv import load_dotenv

load_dotenv()

from engine.db import get_user, register_user, save_score, get_scores, init_db
init_db()  # creates tables on first run

server = Flask(__name__)
server.secret_key = os.getenv("SECRET_KEY", "edugenie_secret_2026")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# PAGE ROUTES
# ──────────────────────────────────────────────

@server.route("/")
def landing():
    return render_template("landing.html")

@server.route("/login")
def login_page():
    return render_template("index.html")

@server.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@server.route("/chat")
def chat():
    return render_template("chat.html")


# ──────────────────────────────────────────────
# AUTH ROUTES
# ──────────────────────────────────────────────

@server.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    user = get_user(username, password)
    if user:
        session["user_id"]  = user["user_id"]
        session["username"] = user["username"]
        session["role"]     = user["role"]
        return jsonify({"status": "success", "role": user["role"], "username": user["username"]})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@server.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role     = data.get("role", "student")

    if not username or not password:
        return jsonify({"status": "error", "message": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400

    success = register_user(username, password, role)
    if success:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Username already exists"}), 400


@server.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})


# ──────────────────────────────────────────────
# PDF UPLOAD
# ──────────────────────────────────────────────

@server.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "message": "Please upload a valid PDF file"}), 400

    filepath  = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)

    text = extract_text_from_pdf(filepath)
    if not text or len(text.strip()) < 50:
        return jsonify({"status": "error", "message": "Could not extract text from PDF"}), 500

    # Cache extracted text (max 15,000 chars for API efficiency)
    text_path = os.path.join(UPLOAD_DIR, "current_pdf.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text[:15000])

    session["pdf_name"] = file.filename

    return jsonify({
        "status":   "success",
        "filename": file.filename,
        "preview":  text[:300]
    })


def get_pdf_text():
    """Read cached PDF text from disk."""
    text_path = os.path.join(UPLOAD_DIR, "current_pdf.txt")
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


# ──────────────────────────────────────────────
# AI FEATURE ROUTES
# ──────────────────────────────────────────────

@server.route("/api/generate-notes", methods=["POST"])
def generate_notes_route():
    pdf_text = get_pdf_text()
    if not pdf_text:
        return jsonify({"status": "error", "message": "No PDF loaded. Please upload a PDF first."}), 400

    notes = generate_notes(pdf_text)
    return jsonify({"status": "success", "notes": notes})


@server.route("/api/generate-quiz", methods=["POST"])
def generate_quiz_route():
    pdf_text = get_pdf_text()
    if not pdf_text:
        return jsonify({"status": "error", "message": "No PDF loaded. Please upload a PDF first."}), 400

    data          = request.get_json() or {}
    num_questions = int(data.get("num_questions", 5))
    num_questions = max(1, min(num_questions, 20))  # clamp 1–20

    quiz = generate_quiz(pdf_text, num_questions)
    return jsonify({"status": "success", "quiz": quiz})


@server.route("/api/chat", methods=["POST"])
def chat_route():
    pdf_text = get_pdf_text() or ""
    data     = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"status": "error", "message": "No question provided"}), 400

    answer = answer_doubt(pdf_text, question)
    return jsonify({"status": "success", "answer": answer})


# ──────────────────────────────────────────────
# ANALYTICS ROUTES
# ──────────────────────────────────────────────

@server.route("/api/save-score", methods=["POST"])
def save_score_route():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    data     = request.get_json() or {}
    score    = data.get("score", 0)
    total    = data.get("total", 0)
    pdf_name = session.get("pdf_name", "Unknown")

    save_score(session["user_id"], pdf_name, score, total)
    return jsonify({"status": "success"})


@server.route("/api/get-scores", methods=["GET"])
def get_scores_route():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    scores = get_scores(session["user_id"])
    return jsonify({"status": "success", "scores": scores})


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)