import type { ScanComparison } from "@/lib/types";

export default function ComparisonCard({ comparison }: { comparison: ScanComparison }) {
  return (
    <div className="comparisonGrid">
      <div>
        <span className="muted">Score atual</span>
        <strong>{comparison.current_score}</strong>
      </div>
      <div>
        <span className="muted">Score anterior</span>
        <strong>{comparison.previous_score ?? "-"}</strong>
      </div>
      <div>
        <span className="muted">Diferença de score</span>
        <strong>{comparison.score_delta === null ? "-" : comparison.score_delta > 0 ? `+${comparison.score_delta}` : comparison.score_delta}</strong>
      </div>
      <div>
        <span className="muted">Diferença de findings</span>
        <strong>{comparison.findings_delta === null ? "-" : comparison.findings_delta}</strong>
      </div>
      <p className="muted wide">{comparison.message}</p>
    </div>
  );
}
