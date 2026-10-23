"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, setToken } from "@/lib/api";
import SectionCard from "@/components/SectionCard";
import { AuthConfigurationNotice, useAuthConfiguration } from "@/components/AuthConfiguration";
import SlowRequestNotice from "@/components/SlowRequestNotice";

export default function LoginPage() {
  const router = useRouter();
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { registrationOpen } = useAuthConfiguration();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api.login({ username_or_email: usernameOrEmail, password });
      setToken(result.access_token);
      router.push("/investigations");
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <div className="grid two">
        <SectionCard title="Entrar">
          <form className="form" onSubmit={handleSubmit}>
            {error && <p className="error">{error}</p>}
            <label htmlFor="login-user">Username ou email</label>
            <input id="login-user" className="input" autoComplete="username" required placeholder="Username ou email" value={usernameOrEmail} onChange={(e) => setUsernameOrEmail(e.target.value)} />
            <label htmlFor="login-password">Palavra-passe</label>
            <input id="login-password" className="input" autoComplete="current-password" required placeholder="Palavra-passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button className="btn primary" disabled={loading}>{loading ? "A entrar..." : "Entrar"}</button>
            <SlowRequestNotice pending={loading} />
            <Link href="/reset-password">Esqueci-me da palavra-passe / Receber acesso</Link>
          </form>
        </SectionCard>
        <SectionCard title={registrationOpen === true ? "Ainda não tens conta?" : "Acesso ao grupo"}>
          <AuthConfigurationNotice />
          {registrationOpen === true ? <>
            <p className="muted">Cria uma conta para guardar histórico de análises e gerar relatórios.</p>
            <Link className="btn" href="/register">Criar conta</Link>
          </> : registrationOpen === false ? <p className="muted">Pede um convite privado ao responsável. Abre o link recebido para definires a tua própria palavra-passe, sem a partilhares. Depois entra com o teu username ou email.</p> : null}
        </SectionCard>
      </div>
    </main>
  );
}
