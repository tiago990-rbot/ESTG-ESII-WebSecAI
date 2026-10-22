"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, getToken, onAuthChanged } from "@/lib/api";
import type { MouseEvent } from "react";
import { useEffect, useState } from "react";

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [logged, setLogged] = useState(false);

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
    <nav className="navbar">
      <Link className="brand" href={logged ? "/investigations" : "/"} onClick={handleBrandClick} aria-label="WebSecAI">
        <span className="brandMark">◆</span>
        <span>WebSecAI</span>
      </Link>
      <div className="navlinks">
        {logged ? (
          <>
            <Link href="/investigations">Investigar</Link>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/history">Histórico</Link>
            <Link href="/profile">Perfil</Link>
            <Link href="/about">Sobre</Link>
            <button className="linkButton" onClick={logout}>Sair</button>
          </>
        ) : (
          <>
            <Link href="/about">Sobre</Link>
            <Link href="/login">Login</Link>
            <Link className="navCta" href="/register">Criar conta</Link>
          </>
        )}
      </div>
    </nav>
  );
}
