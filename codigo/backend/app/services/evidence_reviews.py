"""Human annotations are decisions to audit, never independent proof of an incident."""
import hashlib
import json

def fingerprint(entry):
    content = {key: entry.get(key) for key in ("provider", "category", "title", "description", "source_url", "confirmation", "published_at", "event_at", "meta")}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()

def serialize(review, entry):
    return {"id": review.id, "author_id": review.author_id, "author": review.author.username, "status": review.status, "identity_status": review.identity_status, "note": review.note, "created_at": review.created_at.isoformat(), "is_current": review.evidence_hash == fingerprint(entry)}
