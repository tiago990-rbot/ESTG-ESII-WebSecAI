"use client";

import AuthGuard from "@/components/AuthGuard";
import SectionCard from "@/components/SectionCard";
import { api } from "@/lib/api";
import { formatDate, riskLabel } from "@/lib/scan-helpers";
import type { ScanListItem } from "@/lib/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanListItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listScans().then(setScans).catch((err) => setError(err.message));
  }, []);

  return (
    <AuthGuard>
      <main className="container">
        <h1>Histórico</h1>
        <p className="muted">Todas as análises guardadas para o teu utilizador.</p>
        <SectionCard>
          {error && <p className="error">{error}</p>}
          {scans.length === 0 ? <p className="muted">Ainda não existem análises.</p> : (
            <table className="table">
              <thead><tr><th>Data</th><th>Domínio</th><th>Score</th><th>Risco</th><th>Findings</th><th></th></tr></thead>
              <tbody>
                {scans.map((scan) => (
                  <tr key={scan.id}>
                    <td>{formatDate(scan.created_at)}</td>
                    <td>{scan.domain}</td>
                    <td>{scan.score}</td>
                    <td>{riskLabel(scan.risk_level)}</td>
                    <td>{scan.findings_count}</td>
                    <td><Link className="btn" href={`/history/${scan.id}`}>Detalhe</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </SectionCard>
      </main>
    </AuthGuard>
  );
}
