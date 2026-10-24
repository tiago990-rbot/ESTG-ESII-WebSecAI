"""Explicit source intent; legacy snapshots keep their original scope."""
OPTIONAL_SOURCES = frozenset({"phishtank", "exposure", "hibp_catalog", "urlscan"})
def selected_optional(options):
    if "optional_sources" not in options:
        return {"phishtank", "exposure"}
    return set(options.get("optional_sources", [])) & OPTIONAL_SOURCES
