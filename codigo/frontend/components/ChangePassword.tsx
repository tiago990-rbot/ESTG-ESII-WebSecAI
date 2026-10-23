"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken } from "@/lib/api";
import SectionCard from "./SectionCard";
import SlowRequestNotice from "./SlowRequestNotice";

export default function ChangePassword() {
  const router = useRouter();
  const [current, setCurrent] = useState("");
  const [replacement, setReplacement] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (replacement !== confirmation) { setError("As novas palavras-passe não coincidem."); return; }
    setPending(true);
    try {
      await api.changePassword({ current_password: current, new_password: replacement, confirmation });
      setCurrent(""); setReplacement(""); setConfirmation("");
      setDone(true);
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : "Não foi possível alterar a palavra-passe.");
    } finally { setPending(false); }
  }

  return <SectionCard title="Alterar palavra-passe">
    {done ? <div role="status">
      <p>A palavra-passe foi alterada e todas as sessões anteriores foram terminadas. Entra novamente com a nova palavra-passe.</p>
      <button className="btn primary" onClick={() => { clearToken(); router.push("/login"); }}>Voltar a entrar</button>
    </div> : <form className="form" onSubmit={submit}>
      <p className="muted">Escolhe uma palavra-passe exclusiva, entre 16 e 128 caracteres. A alteração termina as sessões desta conta em todos os dispositivos.</p>
      {error && <p className="error" role="alert">{error}</p>}
      <label htmlFor="change-current">Palavra-passe atual</label>
      <input id="change-current" className="input" type="password" autoComplete="current-password" required maxLength={128} value={current} onChange={e => setCurrent(e.target.value)} />
      <label htmlFor="change-new">Nova palavra-passe</label>
      <input id="change-new" className="input" type="password" autoComplete="new-password" required minLength={16} maxLength={128} value={replacement} onChange={e => setReplacement(e.target.value)} />
      <label htmlFor="change-confirm">Repetir nova palavra-passe</label>
      <input id="change-confirm" className="input" type="password" autoComplete="new-password" required minLength={16} maxLength={128} value={confirmation} onChange={e => setConfirmation(e.target.value)} />
      <button className="btn primary" disabled={pending}>{pending ? "A alterar…" : "Guardar nova palavra-passe"}</button>
      <SlowRequestNotice pending={pending} />
    </form>}
  </SectionCard>;
}
