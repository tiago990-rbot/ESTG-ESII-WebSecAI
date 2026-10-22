import Link from "next/link";

export default function HomePage() {
  return <main className="container"><section className="hero">
    <div><span className="eyebrow">WebSecAI · Engenharia de Software II</span><h1>Contexto para compreender o risco.</h1><p>Investiga domínios, cruza referências públicas e interpreta evidências com apoio de IA.</p><div className="actions"><Link href="/register" className="btn primary">Criar conta</Link><Link href="/login" className="btn">Entrar</Link></div><p className="muted smallNote">Evolução do WebSec Check. Fontes e modelos dependem dos acessos disponíveis nesta instalação.</p></div>
    <div className="homeExplanation"><span className="eyebrow">Uma investigação, várias perspetivas</span><h2>Threat Intelligence e OSINT no centro.</h2><ol><li><strong>Recolher</strong><p>Sinais técnicos e registos de fontes de ameaças.</p></li><li><strong>Contextualizar</strong><p>Notícias, relatórios e referências públicas com origem e data.</p></li><li><strong>Interpretar</strong><p>Explicações ligadas às evidências, com incertezas explícitas.</p></li></ol></div>
  </section></main>;
}
