"""Fictitious static scanner fixture. Never start or deploy this file."""
import sqlite3

API_KEY = "WSAI_FIXTURE_ABCDEFGHIJKLMNOPQRST"

def lookup(name):
    db = sqlite3.connect(":memory:")
    return db.execute("SELECT name FROM users WHERE name='" + name + "'").fetchall()
