"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, setToken } from "@/lib/api";
import SectionCard from "@/components/SectionCard";
import { AuthConfigurationNotice, useAuthConfiguration } from "@/components/AuthConfiguration";
import SlowRequestNotice from "@/components/SlowRequestNotice";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { registrationOpen } = useAuthConfiguration();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (registrationOpen !== true) return;
    setError("");
    setLoading(true);
    try {
      await api.register({ username, email, password });
      const result = await api.login({ username_or_email: username, password });
      setToken(result.access_token);
      router.push("/investigations");
    } catch (err: any) {
      setError(err.message || "Erro ao criar conta");
    } finally {
      setLoading(false);
    }
  }

  if (registrationOpen !== true) return <main className="container">
    <SectionCard title={registrationOpen === false ? "Acesso reservado ao grupo" : "Criação de conta"}>
      <AuthConfigurationNotice />
      {registrationOpen === false ? <p>As contas desta instalação são criadas privadamente pelo responsável do grupo. Se a tua conta já foi criada, podes entrar.</p> : null}
      <div className="actions"><Link className="btn primary" href="/login">Fazer login</Link></div>
    </SectionCard>
  </main>;

  return (
    <main className="container">
      <div className="grid two">
        <SectionCard title="Criar conta">
          <form className="form" onSubmit={handleSubmit}>
            {error && <p className="error">{error}</p>}
            <label htmlFor="register-user">Username</label>
            <input id="register-user" className="input" autoComplete="username" required placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <label htmlFor="register-email">Email</label>
            <input id="register-email" className="input" autoComplete="email" required placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <label htmlFor="register-password">Palavra-passe</label>
            <input id="register-password" className="input" autoComplete="new-password" minLength={8} required placeholder="Palavra-passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button className="btn primary" disabled={loading}>{loading ? "A criar..." : "Criar conta"}</button>
            <SlowRequestNotice pending={loading} />
          </form>
        </SectionCard>
        <SectionCard title="Já tens conta?">
          <p className="muted">Entra para consultar o histórico e criar novas análises.</p>
          <Link className="btn" href="/login">Fazer login</Link>
        </SectionCard>
      </div>
    </main>
  );
}
