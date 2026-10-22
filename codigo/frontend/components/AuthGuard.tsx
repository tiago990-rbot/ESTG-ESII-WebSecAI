"use client";

import { getToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

export default function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return <main className="container"><p>A verificar sessão...</p></main>;
  return <>{children}</>;
}
