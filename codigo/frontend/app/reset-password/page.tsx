"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, clearToken } from "@/lib/api";
import SectionCard from "@/components/SectionCard";
import SlowRequestNotice from "@/components/SlowRequestNotice";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [ready, setReady] = useState(false);
  const [replacement, setReplacement] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    function readLink() {
      const candidate = new URLSearchParams(window.location.hash.slice(1)).get("token") || "";
      // The fragment is never sent to the frontend server; remove it from this history entry.
      window.history.replaceState(window.history.state, "", window.location.pathname);
      if (/^[A-Za-z0-9_-]{43}$/.test(candidate)) {
        setToken(candidate); setDone(false); setError("");
        setReplacement(""); setConfirmation("");
      }
      setReady(true);
    }
    readLink();
    window.addEventListener("hashchange", readLink);
    return () => window.removeEventListener("hashchange", readLink);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (replacement !== confirmation) { setError("As novas palavras-passe não coincidem."); return; }
    setPending(true);
    try {
      await api.resetPassword({ token, new_password: replacement, confirmation });
      setToken(""); setReplacement(""); setConfirmation("");
      clearToken(); setDone(true);
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : "Não foi possível definir a palavra-passe.");
    } finally { setPending(false); }
  }

  return <main className="container"><SectionCard title="Definir palavra-passe">
    {!ready ? <p role="status">A preparar o formulário…</p> : done ? <div role="status">
      <p>A tua palavra-passe foi definida. As sessões anteriores terminaram. Entra com o teu email e a nova palavra-passe.</p>
      <Link className="btn primary" href="/login">Ir para o login</Link>
    </div> : token ? <form className="form" onSubmit={submit}>
      <p className="muted">Define a tua palavra-passe em privado, entre 16 e 128 caracteres. Não a envies ao responsável. O link só funciona uma vez.</p>
      {error && <p className="error" role="alert">{error}</p>}
      <label htmlFor="reset-new">Nova palavra-passe</label>
      <input id="reset-new" className="input" type="password" autoComplete="new-password" required minLength={16} maxLength={128} value={replacement} onChange={e => setReplacement(e.target.value)} />
      <label htmlFor="reset-confirm">Repetir nova palavra-passe</label>
      <input id="reset-confirm" className="input" type="password" autoComplete="new-password" required minLength={16} maxLength={128} value={confirmation} onChange={e => setConfirmation(e.target.value)} />
      <button className="btn primary" disabled={pending}>{pending ? "A guardar…" : "Definir a minha palavra-passe"}</button>
      <SlowRequestNotice pending={pending} />
      <p className="muted">Se fechares ou recarregares esta página antes de concluir, volta a abrir o link original recebido.</p>
    </form> : <div>
      <p>Para criar a tua password ou recuperar o acesso, pede um link privado ao responsável pela instalação. Ele deve confirmar a tua identidade e enviar o link diretamente para ti.</p>
      <p>Esta instalação não envia emails automáticos. Os convites duram 24 horas e os links de reposição duram 30 minutos. Não partilhes o teu link nem a tua password.</p>
      <p>Se já recebeste um link, abre-o completo a partir da mensagem original. Se expirou, pede um novo.</p>
      <Link className="btn" href="/login">Voltar ao login</Link>
    </div>}
  </SectionCard></main>;
}
