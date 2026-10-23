"use client";

import { getToken, onAuthChanged } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

export default function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const sync = () => {
      const hasToken = Boolean(getToken());
      setReady(hasToken);
      if (!hasToken) router.replace("/login");
    };
    sync();
    return onAuthChanged(sync);
  }, [router]);

  if (!ready) return <main className="container"><p>A verificar sessão...</p></main>;
  return <>{children}</>;
}
