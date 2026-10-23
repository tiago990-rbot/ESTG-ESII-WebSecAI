from app.services.incident_groups import candidate_groups


def entry(identifier, url, date=None, **meta):
    return {"id":identifier,"category":"incident_report","title":"Ransomware reportado","description":"Caso fictício", "source_url":url,"event_at":date,"published_at":"2026-01-01","meta":meta}


def test_group_requires_shared_known_event_date_type_and_target():
    rows=[entry("one","https://news.example/one","2025-12-20"),entry("two","https://other.example/two","2025-12-20")]
    result=candidate_groups(rows,"target.example")
    assert result["groups"][0]["evidence_ids"] == ["one","two"]
    assert result["groups"][0]["status"] == "candidate_requires_review"
    assert result["groups"][0]["event_at"] == "2025-12-20"
    assert not candidate_groups([rows[0],dict(rows[1],event_at="2025-12-21")],"target.example")["groups"]


def test_publication_dates_and_homonyms_never_merge_incidents():
    rows=[entry("one","https://news.example/one"),entry("two","https://other.example/two")]
    assert not candidate_groups(rows,"target.example")["groups"]
    rows=[entry("one","https://news.example/one","2025-12-20"),entry("two","https://other.example/two","2025-12-20", matched_by="organization_name",relevance="needs_review")]
    assert not candidate_groups(rows,"target.example")["groups"]


def test_duplicate_source_is_labelled_and_query_identifiers_are_preserved():
    rows=[entry("one","https://news.example/article?id=1#first"),entry("two","https://news.example/article?id=1#second")]
    group=candidate_groups(rows,"target.example")["groups"][0]
    assert group["reason"] == "same_source_url" and group["event_at"] is None
    rows[1]["source_url"]="https://news.example/article?id=2"
    assert not candidate_groups(rows,"target.example")["groups"]


def test_multiple_message_domains_stay_separate_and_invalid_dates_are_unknown():
    rows=[entry("one","https://news.example/one","2025-12-20",queried_domain="one.example"),entry("two","https://other.example/two","2025-12-20",queried_domain="two.example")]
    assert not candidate_groups(rows,"")["groups"]
    for row in rows: row["event_at"]="2025-02-30"
    assert not candidate_groups(rows,"target.example")["groups"]
