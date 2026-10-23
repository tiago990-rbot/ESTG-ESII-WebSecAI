"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, getToken, onAuthChanged } from "@/lib/api";
import type { MouseEvent } from "react";
import { useEffect, useState } from "react";
import { useAuthConfiguration } from "./AuthConfiguration";
import EyeMark from "./EyeMark";

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [logged, setLogged] = useState(false);
  const { registrationOpen } = useAuthConfiguration();

  useEffect(() => {
    const sync = () => setLogged(Boolean(getToken()));
    sync();
    return onAuthChanged(sync);
  }, [pathname]);

  function logout() {
    clearToken();
    setLogged(false);
    router.push("/login");
  }

  function handleBrandClick(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    router.push(logged ? "/investigations" : "/");
  }

  return (
    <nav className="navbar" aria-label="Navegação principal">
      <Link className="brand" href={logged ? "/investigations" : "/"} onClick={handleBrandClick} aria-label="WebSecAI">
        <EyeMark />
        <span>WebSec<span className="brandAI">AI</span><small>THREAT INTELLIGENCE</small></span>
      </Link>
      <div className="navlinks">
        {logged ? (
          <>
            <Link href="/investigations" aria-current={pathname.startsWith("/investigations") ? "page" : undefined}>Investigar</Link>
            <Link href="/dashboard" aria-current={pathname === "/dashboard" ? "page" : undefined}>Análise técnica</Link>
            <Link href="/history" aria-current={pathname.startsWith("/history") ? "page" : undefined}>Histórico técnico</Link>
            <Link href="/profile" aria-current={pathname === "/profile" ? "page" : undefined}>Perfil</Link>
            <Link href="/about" aria-current={pathname === "/about" ? "page" : undefined}>Sobre</Link>
            <button className="linkButton" onClick={logout}>Sair</button>
          </>
        ) : (
          <>
            <Link href="/about" aria-current={pathname === "/about" ? "page" : undefined}>Sobre</Link>
            <Link href="/login" aria-current={pathname === "/login" ? "page" : undefined}>Entrar</Link>
            {registrationOpen === true ? <Link className="navCta" href="/register">Criar conta</Link> : null}
          </>
        )}
      </div>
    </nav>
  );
}
