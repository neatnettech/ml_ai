"""SQLite access for vulnlab — raw sqlite3 on purpose.

We use the low-level sqlite3 driver (not the ORM) so the SQL-injection lessons in
Module 23 are transparent: you can *see* the unsafe string-built query. A real app
would use parameterized queries or an ORM — that is exactly the fix you apply later.
"""
from __future__ import annotations

import os
import sqlite3

DB_PATH = os.getenv("VULNLAB_DB", os.path.join(os.path.dirname(__file__), "vulnlab.db"))


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db(reset: bool = True) -> None:
    """Create tables and seed demo data. Called on app startup.

    Passwords are stored in PLAINTEXT here — itself a vulnerability you will fix in
    Module 24. Never do this in a real system (see Module 18/19 for bcrypt).
    """
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = connect()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE users (
            id        INTEGER PRIMARY KEY,
            username  TEXT UNIQUE,
            password  TEXT,           -- plaintext on purpose (vuln)
            role      TEXT,
            api_token TEXT             -- "secret" to exfiltrate via SQLi
        );
        CREATE TABLE notes (
            id       INTEGER PRIMARY KEY,
            owner    TEXT,
            title    TEXT,
            body     TEXT,
            private  INTEGER           -- 1 = should only be visible to owner
        );
        CREATE TABLE comments (
            id     INTEGER PRIMARY KEY,
            author TEXT,
            body   TEXT                 -- rendered unescaped (stored XSS)
        );
        """
    )

    users = [
        ("alice", "hunter2", "admin", "tok_alice_9f3c1a"),
        ("bob", "password123", "user", "tok_bob_22b7de"),
        ("carol", "letmein", "user", "tok_carol_aa01ff"),
    ]
    cur.executemany(
        "INSERT INTO users (username, password, role, api_token) VALUES (?, ?, ?, ?)",
        users,
    )

    notes = [
        ("alice", "Launch checklist", "Ship the thing on Friday.", 0),
        ("alice", "Admin master key", "ADMIN-KEY=ZmxhZ3thZG1pbn0", 1),  # private!
        ("bob", "Grocery list", "Milk, eggs, bread.", 0),
        ("bob", "Bank PIN reminder", "It's 4821 (do not tell anyone).", 1),  # private!
        ("carol", "Book ideas", "A novel about a packet that got lost.", 0),
    ]
    cur.executemany(
        "INSERT INTO notes (owner, title, body, private) VALUES (?, ?, ?, ?)",
        notes,
    )

    conn.commit()
    conn.close()
