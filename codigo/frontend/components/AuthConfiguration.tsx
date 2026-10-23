"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import SlowRequestNotice from "./SlowRequestNotice";

type Availability = {
  registrationOpen: boolean | null;
  loading: boolean;
  failed: boolean;
  retry: () => void;
};
const Context = createContext<Availability | null>(null);

export function AuthConfigurationProvider({ children }: { children: ReactNode }) {
  const [registrationOpen, setRegistrationOpen] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setRegistrationOpen(null);
    setLoading(true);
    setFailed(false);
    const timeout = setTimeout(() => controller.abort(), 90_000);
    void api.authConfiguration(controller.signal).then((policy) => {
      if (typeof policy.public_registration_enabled !== "boolean") throw new Error("Invalid policy");
      if (active) setRegistrationOpen(policy.public_registration_enabled);
    }).catch(() => {
      if (active) setFailed(true);
    }).finally(() => {
      clearTimeout(timeout);
      if (active) setLoading(false);
    });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [attempt]);

  return <Context.Provider value={{ registrationOpen, loading, failed, retry: () => setAttempt((value) => value + 1) }}>
    {children}
  </Context.Provider>;
}

export function useAuthConfiguration() {
  const value = useContext(Context);
  if (!value) throw new Error("AuthConfigurationProvider ausente");
  return value;
}

export function AuthConfigurationNotice() {
  const { loading, failed, retry } = useAuthConfiguration();
  if (failed) return <div className="notice" role="status">
    <p>Não foi possível confirmar se a criação de contas está disponível. Podes tentar entrar com uma conta existente.</p>
    <button type="button" className="btn" onClick={retry}>Voltar a verificar</button>
  </div>;
  if (loading) return <div>
    <p className="muted" role="status">A confirmar a disponibilidade do registo…</p>
    <SlowRequestNotice pending={loading} />
  </div>;
  return null;
}
