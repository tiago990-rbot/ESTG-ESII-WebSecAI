"use client";

import AuthGuard from "@/components/AuthGuard";
import SectionCard from "@/components/SectionCard";
import StatCard from "@/components/StatCard";
import { api } from "@/lib/api";
import type { ScanListItem, ScanStats } from "@/lib/types";
import { riskLabel } from "@/lib/scan-helpers";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

export default function DashboardPage() {
  const router = useRouter();
  const [url, setUrl] = useState("example.com");
  const [stats, setStats] = useState<ScanStats | null>(null);
  const [scans, setScans] = useState<ScanListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadData() {
    const [statsData, scansData] = await Promise.all([api.stats(), api.listScans()]);
    setStats(statsData);
    setScans(scansData.slice(0, 5));
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleScan(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const result = await api.createScan(url, authorized);
      setSuccess(`Análise concluída com sucesso. A abrir o detalhe...`);
      await loadData();
      router.push(`/history/${result.scan_id}`);
    } catch (err: any) {
      setError(err.message || "Erro ao criar scan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <main className="container">
        <div className="dashboardIntro">
          <div>
            <span className="eyebrow">Painel principal</span>
            <h1>Dashboard</h1>
            <p className="muted">Cria análises, acompanha scores e consulta o histórico de segurança.</p>
          </div>
          <Link className="btn" href="/history">Ver histórico completo</Link>
        </div>

        <div className="statGrid">
          <StatCard title="Total de scans" value={stats?.total_scans ?? 0} description="Análises guardadas" />
          <StatCard title="Score médio" value={stats?.average_score ?? 0} description="Média do histórico" />
          <StatCard title="Melhor score" value={stats?.best_score ?? "-"} description="Melhor resultado" />
          <StatCard title="Pior score" value={stats?.worst_score ?? "-"} description="Resultado mais baixo" />
        </div>

        <SectionCard title="Nova análise de website">
          <form className="form" onSubmit={handleScan}>
            <label htmlFor="legacy-target">Domínio do website</label>
            <input id="legacy-target" className="input" placeholder="example.com" value={url} onChange={(e) => setUrl(e.target.value)} />
            <label className="checkLabel"><input type="checkbox" required checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /> O website é meu ou tenho autorização para estas verificações.</label>
            <button className="btn primary" disabled={loading}>{loading ? "A analisar..." : "Analisar website"}</button>
          </form>
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}
          <div className="quickTargets">
            <span className="muted">Exemplos rápidos:</span>
            {["example.com", "wikipedia.org", "google.com"].map((target) => (
              <button key={target} type="button" className="quickTarget" onClick={() => setUrl(target)}>{target}</button>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Últimas análises">
          {scans.length === 0 ? <p className="muted">Ainda não existem análises.</p> : (
            <table className="table">
              <thead><tr><th>Domínio</th><th>Score</th><th>Risco</th><th></th></tr></thead>
              <tbody>
                {scans.map((scan) => (
                  <tr key={scan.id}>
                    <td>{scan.domain}</td>
                    <td>{scan.score}</td>
                    <td>{riskLabel(scan.risk_level)}</td>
                    <td><Link className="btn" href={`/history/${scan.id}`}>Abrir</Link></td>
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
