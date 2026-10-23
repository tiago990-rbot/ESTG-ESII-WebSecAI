"use client";

import AnalysisDashboard from "@/components/AnalysisDashboard";
import AuthGuard from "@/components/AuthGuard";
import ComparisonCard from "@/components/ComparisonCard";
import FindingsList from "@/components/FindingsList";
import ScorePanel from "@/components/ScorePanel";
import SectionCard from "@/components/SectionCard";
import { api, downloadReport } from "@/lib/api";
import { formatDate } from "@/lib/scan-helpers";
import type { ScanComparison, ScanDetail } from "@/lib/types";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function ScanDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const [scan, setScan] = useState<ScanDetail | null>(null);
  const [comparison, setComparison] = useState<ScanComparison | null>(null);
  const [error, setError] = useState("");
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    Promise.all([api.getScan(id), api.comparison(id)])
      .then(([scanData, comparisonData]) => {
        setScan(scanData);
        setComparison(comparisonData);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  return (
    <AuthGuard>
      <main className="container">
        {error && <p className="error">{error}</p>}
        {!scan ? <p>A carregar...</p> : (
          <div className="grid">
            <div className="detailHeader">
              <div>
                <Link className="muted backLink" href="/history">← Voltar ao histórico</Link>
                <h1>{scan.domain}</h1>
                <p className="muted">Análise criada em {formatDate(scan.created_at)}</p>
              </div>
              <button className="btn primary" onClick={() => downloadReport(scan.id)}>Exportar PDF</button>
            </div>

            <SectionCard>
              <ScorePanel score={scan.score} riskLevel={scan.risk_level} />
              <p className="summaryText">{scan.summary}</p>
            </SectionCard>

            <AnalysisDashboard scan={scan} />

            {comparison && (
              <SectionCard title="Comparação com análise anterior">
                <ComparisonCard comparison={comparison} />
              </SectionCard>
            )}

            <SectionCard title="Findings e recomendações">
              <FindingsList findings={scan.findings} />
            </SectionCard>

            <SectionCard title="Detalhes técnicos completos">
              <p className="muted">Esta zona mostra o JSON técnico completo guardado na base de dados.</p>
              <button className="btn" onClick={() => setShowRaw((value) => !value)}>
                {showRaw ? "Esconder JSON" : "Mostrar JSON"}
              </button>
              {showRaw && <pre className="detailsBox">{JSON.stringify(scan.details, null, 2)}</pre>}
            </SectionCard>
          </div>
        )}
      </main>
    </AuthGuard>
  );
}
