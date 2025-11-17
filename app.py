import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from tempfile import mkdtemp
from helpers import apology, login_required
import spacy
from spacy import displacy
from io import BytesIO

# Initialise application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Database setup


def get_db_connection():
    conn = sqlite3.connect("syntactica.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    text = request.form.get("text")
    feature = request.form.get("feature")

    if not text:
        return apology("Please  enter text.")

    doc = nlp(text)

    # Dependency parse → SVG
    if feature == "dep":
        html = displacy.render(doc, style="dep", page=True)

        # Save history
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO analyses (user_id, input_text, analysis_type, result_svg)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], text, "Dependency Parse", html))
        conn.commit()
        conn.close()

        return render_template("result.html",
                               result_type="Dependency Parse",
                               html=html)

    # TOKENS
    elif feature == "tokens":
        tokens = [token.text for token in doc]

        # save history (no SVG)
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO analyses (user_id, input_text, analysis_type)
            VALUES (?, ?, ?)
        """, (session["user_id"], text, "Tokens"))
        conn.commit()
        conn.close()

        return render_template("result.html",
                               result_type="Tokens",
                               items=tokens)

    # LEMMAS
    elif feature == "lemmas":
        lemmas = [token.lemma_ for token in doc]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO analyses (user_id, input_text, analysis_type)
            VALUES (?, ?, ?)
        """, (session["user_id"], text, "Lemmas"))
        conn.commit()
        conn.close()

        return render_template("result.html",
                               result_type="Lemmas",
                               items=lemmas)

    # REMOVE STOPWORDS
    elif feature == "nostop":
        filtered = [token.text for token in doc if not token.is_stop]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO analyses (user_id, input_text, analysis_type)
            VALUES (?, ?, ?)
        """, (session["user_id"], text, "No Stopwords"))
        conn.commit()
        conn.close()

        return render_template("result.html",
                               result_type="Text without Stopwords",
                               items=filtered)

    else:
        return apology("Invalid option selected.")


# DB Insert Function
def save_analysis(input_text, analysis_type, result_svg):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO analyses (user_id, input_text, analyses_type, result_svg) VALUES (?, ?, ?, ?)",
        (session["user_id"], input_text, analysis_type, result_svg)
    )
    conn.commit()
    conn.close()

# HISTORY PAGE


@app.route("/history", methods=["GET"])
@login_required
def history():
    conn = get_db_connection()
    analyses = conn.execute(
        "SELECT * FROM analyses WHERE user_id = ? ORDER BY timestamp DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("history.html", analyses=analyses)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("All fields are required.")

        if password != confirmation:
            return apology("Passwords do not match.")

        hash_pw = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hash_pw))
            conn.commit()
        except:
            return apology("Username already exists.")
        finally:
            conn.close()

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return apology("Username and password required.")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["hash"], password):
            return apology("Invalid username or password.")

        session["user_id"] = user["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/download_dep", methods=["POST"])
@login_required
def download_dep():
    text = request.form.get("text")
    if not text:
        return apology("No text provided to download visualization.")

    doc = nlp(text)
    html = displacy.render(doc, style="dep", page=True)
    buffer = BytesIO()
    buffer.write(html.encode("utf-8"))
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="dependency.html", mimetype="text/html")


if __name__ == "__main__":
    # Create users table if not exists
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    app.run(debug=True)
