import { riskLabel, scoreMessage } from "@/lib/scan-helpers";

export default function ScorePanel({ score, riskLevel }: { score: number; riskLevel: string }) {
  const riskClass = riskLevel === "good" ? "good" : riskLevel === "medium" ? "medium" : "weak";

  return (
    <div className="scorePanel">
      <div className={`scoreCircle ${riskClass}`}>{score}</div>
      <div>
        <p className="muted">Score de segurança</p>
        <h2>{scoreMessage(score)}</h2>
        <p>Nível de risco: <span className={`riskPill ${riskClass}`}>{riskLabel(riskLevel)}</span></p>
      </div>
    </div>
  );
}
