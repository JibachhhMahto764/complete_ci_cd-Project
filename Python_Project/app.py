from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.environ.get("DATABASE", "data.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    conn = get_db()

    if search:
        records = conn.execute("""
            SELECT * FROM records
            WHERE name LIKE ?
               OR email LIKE ?
               OR category LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()
    else:
        records = conn.execute("""
            SELECT * FROM records
            ORDER BY id DESC
        """).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM records"
    ).fetchone()[0]

    active = conn.execute(
        "SELECT COUNT(*) FROM records WHERE status = 'Active'"
    ).fetchone()[0]

    inactive = conn.execute(
        "SELECT COUNT(*) FROM records WHERE status = 'Inactive'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        records=records,
        total=total,
        active=active,
        inactive=inactive,
        search=search
    )


@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    category = request.form.get("category", "").strip()
    status = request.form.get("status", "Active")
    notes = request.form.get("notes", "").strip()

    if not name or not email or not category:
        return redirect(url_for("index"))

    conn = get_db()

    conn.execute("""
        INSERT INTO records
        (name, email, category, status, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        email,
        category,
        status,
        notes
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/edit/<int:record_id>")
def edit_page(record_id):
    conn = get_db()

    record = conn.execute(
        "SELECT * FROM records WHERE id = ?",
        (record_id,)
    ).fetchone()

    conn.close()

    if record is None:
        return "Record not found", 404

    return render_template("edit.html", record=record)


@app.route("/edit/<int:record_id>", methods=["POST"])
def edit_record(record_id):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    category = request.form.get("category", "").strip()
    status = request.form.get("status", "Active")
    notes = request.form.get("notes", "").strip()

    conn = get_db()

    conn.execute("""
        UPDATE records
        SET name = ?,
            email = ?,
            category = ?,
            status = ?,
            notes = ?
        WHERE id = ?
    """, (
        name,
        email,
        category,
        status,
        notes,
        record_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM records WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api/records")
def api_records():
    conn = get_db()

    records = conn.execute("""
        SELECT * FROM records
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(record)
        for record in records
    ])


if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
