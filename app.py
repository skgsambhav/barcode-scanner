import os
import sqlite3
from flask import Flask, render_template, request, jsonify, g

# -------- Config --------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Render पर भी local SQLite ठीक है (demo). चाहें तो env से path दे सकते हैं.
DB_PATH = os.environ.get("DB_PATH", os.path.join(APP_DIR, "app.db"))

app = Flask(__name__)

# -------- DB Helpers --------
def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_schema_and_seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            barcode TEXT UNIQUE,
            sku     TEXT UNIQUE,
            price   REAL
        )""")
        # Demo row (safe upsert style)
        con.execute("""
        INSERT OR IGNORE INTO products (name, barcode, sku, price)
        VALUES (?,?,?,?)
        """, ("Sample Item", "8901234567890", "SKU-001", 199.0))

# -------- Routes --------
@app.route("/")
def home():
    return "<a href='/scan'>Open Scanner</a>"

@app.route("/scan")
def scan():
    return render_template("scan.html")

@app.route("/api/search")
def api_search():
    code = (request.args.get("code") or "").strip()
    if not code:
        return jsonify({"ok": False, "error": "code missing"}), 400

    db = get_db()
    row = db.execute("""
        SELECT id, name, barcode, sku, price
        FROM products
        WHERE barcode = ? OR sku = ?
        LIMIT 1
    """, (code, code)).fetchone()

    if not row:
        return jsonify({"ok": True, "found": False, "code": code})

    return jsonify({"ok": True, "found": True, "data": dict(row)})

# Render health check (optional)
@app.route("/health")
def health():
    return "ok", 200

# -------- App init --------
ensure_schema_and_seed()

if __name__ == "__main__":
    # Local dev के लिए run; Render पर gunicorn app:app चलाएगा
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
