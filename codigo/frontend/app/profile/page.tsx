"use client";

import AuthGuard from "@/components/AuthGuard";
import SectionCard from "@/components/SectionCard";
import StatCard from "@/components/StatCard";
import ChangePassword from "@/components/ChangePassword";
import { api } from "@/lib/api";
import { formatDate, riskLabel } from "@/lib/scan-helpers";
import type { ScanListItem, ScanStats, User } from "@/lib/types";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

function initials(username?: string) {
  if (!username) return "U";
  return username.slice(0, 2).toUpperCase();
}

function activityLabel(total: number) {
  if (total === 0) return "Ainda sem análises";
  if (total < 3) return "A começar";
  if (total < 10) return "Utilizador ativo";
  return "Utilizador avançado";
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<ScanStats | null>(null);
  const [scans, setScans] = useState<ScanListItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.me(), api.stats(), api.listScans()])
      .then(([u, s, list]) => {
        setUser(u);
        setStats(s);
        setScans(list);
      })
      .catch((err) => setError(err.message || "Erro ao carregar perfil"));
  }, []);

  const totalFindings = useMemo(() => scans.reduce((sum, scan) => sum + (scan.findings_count || 0), 0), [scans]);
  const latest = scans[0];
  const topDomain = stats?.top_domains?.[0];
  const totalScans = stats?.total_scans ?? 0;

  return (
    <AuthGuard>
      <main className="container">
        {error && <p className="error">{error}</p>}

        <section className="profileHero card">
          <div className="avatarCircle">{initials(user?.username)}</div>
          <div className="profileHeroInfo">
            <span className="eyebrow">Perfil do utilizador</span>
            <h1>{user?.username || "A carregar..."}</h1>
            <p className="muted">{user?.email || "A obter dados da conta..."}</p>
            <div className="profileBadges">
              <span>{activityLabel(totalScans)}</span>
              <span>Conta criada em {formatDate(user?.created_at)}</span>
              <span>{totalScans} análises guardadas</span>
            </div>
          </div>
          <div className="profileHeroActions">
            <Link className="btn primary" href="/dashboard">Nova análise</Link>
            <Link className="btn" href="/history">Ver histórico</Link>
          </div>
        </section>

        <div className="statGrid profileStats">
          <StatCard title="Total de scans" value={totalScans} description="Análises feitas por este utilizador" />
          <StatCard title="Score médio" value={stats?.average_score ?? 0} description="Média dos resultados guardados" />
          <StatCard title="Melhor score" value={stats?.best_score ?? "-"} description="Melhor postura analisada" />
          <StatCard title="Findings totais" value={totalFindings} description="Alertas encontrados no histórico" />
        </div>

        <div className="grid two">
          <SectionCard title="Resumo da conta">
            <div className="profileInfoList">
              <div><span>Username</span><strong>{user?.username || "-"}</strong></div>
              <div><span>Email</span><strong>{user?.email || "-"}</strong></div>
              <div><span>Data de criação</span><strong>{formatDate(user?.created_at)}</strong></div>
              <div><span>Última análise</span><strong>{formatDate(stats?.last_scan_date)}</strong></div>
            </div>
          </SectionCard>

          <SectionCard title="Domínios mais analisados">
            {!stats?.top_domains?.length ? (
              <p className="muted">Ainda não existem domínios analisados.</p>
            ) : (
              <div className="domainList">
                {stats.top_domains.map((item) => (
                  <div key={item.domain}>
                    <span>{item.domain}</span>
                    <strong>{item.count}x</strong>
                  </div>
                ))}
              </div>
            )}
            {topDomain && <p className="muted smallNote">Domínio mais frequente: {topDomain.domain}</p>}
          </SectionCard>
        </div>

        <ChangePassword />

        <SectionCard title="Últimas análises deste utilizador">
          {scans.length === 0 ? (
            <div className="emptyState">
              <h3>Ainda não existem análises</h3>
              <p className="muted">Cria a primeira análise no dashboard para começar a preencher o perfil.</p>
              <Link className="btn primary" href="/dashboard">Criar primeira análise</Link>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr><th>Domínio</th><th>Score</th><th>Risco</th><th>Findings</th><th>Data</th><th></th></tr>
              </thead>
              <tbody>
                {scans.slice(0, 6).map((scan) => (
                  <tr key={scan.id}>
                    <td>{scan.domain}</td>
                    <td>{scan.score}</td>
                    <td>{riskLabel(scan.risk_level)}</td>
                    <td>{scan.findings_count}</td>
                    <td>{formatDate(scan.created_at)}</td>
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
