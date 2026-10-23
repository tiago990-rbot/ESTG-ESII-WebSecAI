"use client";

import { useEffect, useState } from "react";

export default function SlowRequestNotice({ pending }: { pending: boolean }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!pending) return;
    const timer = setTimeout(() => setSlow(true), 4_000);
    return () => clearTimeout(timer);
  }, [pending]);
  if (!pending || !slow) return null;
  return <p className="notice" role="status">O servidor pode estar a iniciar. O primeiro acesso pode demorar cerca de um minuto; aguarda sem voltar a enviar o formulário.</p>;
}
