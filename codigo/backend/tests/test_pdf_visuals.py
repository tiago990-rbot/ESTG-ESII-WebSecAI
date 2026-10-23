"""Printed views must preserve provenance, date precision and unknowns."""
from copy import deepcopy
from datetime import timezone
from evaluations.report_fixture import snapshot
from app.services.investigation_pdf import investigation_pdf
from app.services.investigation_pdf_visuals import graph_data, parsed_date, relation, timeline_data


def test_print_timeline_never_substitutes_publication_or_catalog_for_incident():
    entries = snapshot()["evidence"]
    entries[0]["meta"]["catalog_added_at"] = "2025-01-01"
    index = {entry["id"]: i + 1 for i, entry in enumerate(entries)}
    before = deepcopy(entries)
    lanes = {lane["field"]: lane for lane in timeline_data(entries, index)}
    assert lanes["published_at"]["dated"] == 1
    assert lanes["event_at"]["dated"] == 0
    assert lanes["event_at"]["unknown"] == list(range(1, 8))
    assert lanes["observed_at"]["dated"] == 7
    assert lanes["published_at"]["groups"][0]["label"] == "01/10/2026"
    assert lanes["observed_at"]["groups"][0]["numbers"] == list(range(1, 8))
    assert entries == before


def test_timeline_rejects_bad_dates_and_preserves_timezone_and_calendar_precision():
    assert parsed_date("2026-02-30") is None
    assert parsed_date("2026-13-01T00:00:00Z") is None
    assert parsed_date("2026-W42-1") is None
    assert parsed_date(None) is None
    assert parsed_date("yesterday") is None
    moment, label = parsed_date("2026-10-23T01:30:00+02:00")
    assert moment.tzinfo == timezone.utc and label == "22/10/2026 23:30 UTC"
    assert parsed_date("2026-10-23")[1] == "23/10/2026"


def test_timeline_groups_and_bounds_visually_without_losing_unknown_counts():
    base = snapshot()["evidence"][0]
    entries = [dict(base, id=str(i), published_at=f"2026-10-{i + 1:02d}") for i in range(12)]
    entries.append(dict(base, id="bad", published_at="invalid"))
    index = {entry["id"]: i + 1 for i, entry in enumerate(entries)}
    lane = timeline_data(entries, index)[0]
    assert [group["label"] for group in lane["groups"]] == [f"{i:02d}/10/2026" for i in range(12, 7, -1)]
    assert lane["omitted_groups"] == 7 and lane["unknown"] == [13]
    assert lane["dated"] == 12


def test_map_is_balanced_bounded_and_has_only_collection_edges():
    base = snapshot()["evidence"]
    entries = [dict(base[4], id="tech-" + str(i)) for i in range(40)] + base + [base[0]]
    original = deepcopy(entries)
    view = graph_data(entries)
    assert len(view["entries"]) == len(view["edges"]) == 24
    assert {entry["provider"] for entry in view["entries"]} == {"osint", "urlhaus", "kev", "technical"}
    assert {edge["kind"] for edge in view["edges"]} == {"collected_by"}
    assert view["total"] == 47 and view["omitted"] == 23
    assert entries == original


def test_uncertain_general_and_previous_entries_are_not_presented_as_confirmed_links():
    base = snapshot()["evidence"][0]
    for updates, expected in [
        ({"category": "kev_general"}, "Alerta geral"),
        ({"category": "kev_candidate"}, "Candidato por produto"),
        ({"meta": {"matched_by": "organization_name"}}, "Relação por verificar"),
        ({"meta": {"retained_from_earlier_attempt": True}}, "Resultado anterior"),
        ({"confirmation": "allegation"}, "Alegação"),
        ({"confirmation": "unverified"}, "Conteúdo por verificar"),
    ]:
        assert relation(dict(base, **updates)) == (expected, True)


def test_pdf_handles_dense_dates_long_titles_multipage_map_and_missing_current_report():
    data = snapshot()
    base = data["evidence"]
    data["evidence"] = [dict(base[i % len(base)], id="entry-" + str(i), title="Título & <não confiável> " * 25) for i in range(50)]
    data["reports"] = []
    assert investigation_pdf(data).startswith(b"%PDF")
    data["previous_evidence"] = data["evidence"]
    data["evidence"] = []
    assert investigation_pdf(data).startswith(b"%PDF")
