"""Controlled comparison fixture; no credential marker or SQL interpolation."""
import sqlite3

def lookup(name):
    db = sqlite3.connect(":memory:")
    return db.execute("SELECT name FROM users WHERE name=?", (name,)).fetchall()
