import type { Finding } from "@/lib/types";
import { severityLabel } from "@/lib/scan-helpers";

export default function FindingsList({ findings }: { findings: Finding[] }) {
  if (!findings || findings.length === 0) {
    return <p className="muted">Nenhum finding encontrado.</p>;
  }

  return (
    <div className="findingsList">
      {findings.map((finding) => (
        <article className="finding" key={finding.id}>
          <div className="findingHeader">
            <h3>{finding.title}</h3>
            <span className={`badge ${finding.severity}`}>{severityLabel(finding.severity)}</span>
          </div>
          <p className="muted">Categoria: {finding.category}</p>
          <p>{finding.description}</p>
          <p><strong>Recomendação:</strong> {finding.recommendation}</p>
        </article>
      ))}
    </div>
  );
}
