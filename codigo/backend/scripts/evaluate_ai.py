"""Opt-in real model evaluation with fictional evidence. No external searches."""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluations.cases import cases
from app.services import ai_service, providers
from app.services.coverage import summarize_coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Allow bounded Groq calls with synthetic inputs")
    parser.add_argument("--case", choices=[case["id"] for case in cases()], action="append")
    parser.add_argument("--label", default="current", choices=["baseline", "current"])
    parser.add_argument("--interval", type=int, default=0, choices=range(0,61), metavar="0..60")
    parser.add_argument("--window-budget", type=Path)
    args = parser.parse_args()
    if args.window_budget:
        os.environ["WEBSECAI_REQUEST_WINDOW_FILE"] = str(args.window_budget.resolve())
    selected = [case for case in cases() if not args.case or case["id"] in args.case]
    if not args.live:
        print(json.dumps({"mode": "dry_run", "calls": 0, "cases": [case["id"] for case in selected]}))
        return
    records = []
    original_request = providers.json_request
    calls = []
    def counted_request(method, url, **kwargs):
        calls.append(True)
        return original_request(method, url, **kwargs)
    providers.json_request = counted_request
    for index, case in enumerate(selected):
        if index and args.interval:
            time.sleep(args.interval)
        before = len(calls)
        record = {"case": case["id"], "expected": case["expected"]}
        try:
            report, model = ai_service.generate(case["evidence"], case["target"], case["runs"], case.get("question", ""))
            record.update(status="generated", schema_and_reference_ids_valid=True, model=model,
                          prompt_version=ai_service.PROMPT_VERSION, report=report, manual_review="pending")
        except providers.SourceError as exc:
            record.update(status=exc.status, message=exc.message, diagnostics=exc.diagnostics)
            if exc.status == "no_results":
                record.update(status="insufficient_target_evidence_no_model_call", coverage=summarize_coverage(case["evidence"], case["runs"]))
        except ValidationError as exc:
            fields = {"summary", "observations", "recommendations", "limitations", "text", "evidence_ids"}
            record.update(status="schema_rejected", schema_errors=[{"type": entry["type"], "fields": [part for part in entry["loc"] if part in fields]} for entry in exc.errors()[:8]])
        except json.JSONDecodeError:
            record.update(status="malformed_json_rejected")
        except ValueError:
            record.update(status="invalid_references_rejected")
        except Exception:
            record.update(status="invalid_or_unavailable_response")
        record["external_model_requests"] = len(calls) - before
        records.append(record)
        print(json.dumps({"case": case["id"], "status": record["status"]}), flush=True)
        if record["status"] == "rate_limited":
            break
    folder = ROOT.parent.parent / "registos" / "avaliacao_ia"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / (stamp + "-" + args.label + ".json")
    path.write_text(json.dumps({"mode": "live_model_synthetic_evidence", "external_searches": 0,
                               "prompt_sha256": hashlib.sha256(ai_service.SYSTEM.encode()).hexdigest(),
                               "created_at": datetime.now(timezone.utc).isoformat(),
                               "results": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"record": str(path), "generated": sum(r["status"] == "generated" for r in records), "cases": len(records)}))


if __name__ == "__main__":
    main()
