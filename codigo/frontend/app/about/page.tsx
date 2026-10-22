import SectionCard from "@/components/SectionCard";

export default function AboutPage() {
  return (
    <main className="container">
      <h1>Sobre o WebSecAI</h1>
      <p className="muted">Projeto de Engenharia de Software II, desenvolvido sobre o WebSec Check do ano anterior.</p>
      <div className="grid two">
        <SectionCard title="Objetivo">
          <p>
            O WebSecAI reúne Threat Intelligence, notícias e referências públicas a incidentes, verificações técnicas autorizadas e uma síntese IA com ligações às evidências.
            Cada fonte mostra a sua cobertura e disponibilidade. Uma alegação num fórum exige confirmação e um alerta geral de exploração não comprova um ataque ao website.
          </p>
        </SectionCard>
        <SectionCard title="Funcionalidades">
          <ul>
            <li>Registo e login de utilizadores</li>
            <li>Histórico individual de análises</li>
            <li>Análise DNS, TLS e HTTP</li>
            <li>Score e findings com recomendações</li>
            <li>Comparação com análise anterior</li>
            <li>Relatório PDF</li>
            <li>Reputação de URLs e pesquisa pública de incidentes</li>
            <li>Alertas de exploração conhecida do catálogo CISA KEV</li>
            <li>Análise de sinais em mensagens suspeitas</li>
            <li>Síntese e perguntas por IA, quando o acesso estiver configurado</li>
          </ul>
        </SectionCard>
      </div>

      <div className="grid two aboutGrid">
        <SectionCard title="Como o score é calculado">
          <p>O score começa em 100 pontos e perde pontos quando a aplicação não confirma determinadas boas práticas.</p>
          <ul>
            <li>DNS ou HTTPS indisponível têm impacto elevado.</li>
            <li>Certificado expirado ou inválido tem impacto elevado.</li>
            <li>Headers ausentes reduzem o score conforme a importância.</li>
            <li>Cookies sem atributos de segurança reduzem o score quando existem cookies.</li>
            <li>Headers que expõem tecnologia têm impacto baixo.</li>
          </ul>
        </SectionCard>
        <SectionCard title="Como interpretar os findings">
          <p>
            Um finding não significa automaticamente que o site está vulnerável. Significa que, na resposta pública analisada,
            a aplicação não conseguiu confirmar uma proteção recomendada ou encontrou um sinal de melhoria.
          </p>
          <p>
            Em sites grandes, como motores de pesquisa ou plataformas globais, algumas proteções podem ser aplicadas por rota,
            por domínio, por camada interna ou por mecanismos diferentes dos headers verificados nesta ferramenta.
          </p>
        </SectionCard>
      </div>

      <SectionCard title="Limitações assumidas">
        <p>
          Esta ferramenta académica reúne observações e referências com cobertura limitada. A demonstração usa dados fictícios identificados; as integrações reais dependem do acesso às fontes. Os resultados técnicos dependem da resposta recebida no momento da análise,
          do domínio escolhido, de redirecionamentos, bloqueios, localização, CDN e políticas específicas do servidor. Por isso, os resultados
          devem ser explicados como indicadores de postura de segurança e não como uma certificação completa de segurança.
        </p>
      </SectionCard>
    </main>
  );
}
