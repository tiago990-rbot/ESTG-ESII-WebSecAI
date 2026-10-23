# Validação da publicação — v7 integrada, 23/10/2026

## Resultado atual

As melhorias v6/v7 do Gonçalo foram acrescentadas à v5 e publicadas nos serviços existentes. Interface: **https://websecai-frontend.websecai-estg.workers.dev**. API: **https://websecaiapi.onrender.com**.

A publicação passou nos testes públicos de disponibilidade, política de registo e CORS. **Não está concluída a aceitação autenticada remota:** faltam confirmação de contas reais, login/demonstração/PDF/isolamento no alojamento e rotação privada da credencial Neon exposta. A adequação sustentada ao Cloudflare Free continua por resolver. Não confundir deploy Live, testes controlados ou exemplo fictício com aceitação de fornecedores, IA ou disponibilidade garantida.

## O que foi integrado

A receção v7 continha38 ficheiros de código cumulativos. Foram conferidos por hashes contra a base original ou o after-hash da v5 já integrada. Apenas18 precisaram de alteração/adição; os restantes foram preservados. Adaptaram-se ainda os dois harnesses de navegador à demonstração completa com sete evidências e às seis respostas expansíveis. Foram preservados PostgreSQL, TLS, migrações diretas, autorização por dono, contas internas, quotas e alojamento. Nenhuma nova dependência, migração ou tabela.

- Contrato analyst-v4-intelligence: conclusões/observações, inferências e hipóteses, correlações com referências, seis perguntas, prioridades verificáveis e lacunas. Validação local de referências e confiança conservadora; não é verificação semântica integral.
- Dossiê público ou completo com análise técnica, esta apenas mediante autorização explícita. A demonstração completa usa sete referências fictícias e não executa análises de alvos.
- Seleção equilibrada até24 evidências para IA, preservando dados integrais no dossiê. Metadados técnicos minimizados. O máximo de saída é4600tokens; quotas/reservas não foram aumentadas. Testes reais Groq/Tavily exigem pequeno orçamento confirmado.
- PDF profissional com identidade vetorial, conclusões, perguntas, prioridades, contexto, cobertura, cronologia de publicação/incidente/consulta, mapa de proveniência e anexo. Exportar usa o snapshot guardado, sem recolha ou geração de IA adicional. Sínteses antigas/desatualizadas e resultados conservados mantêm avisos; datas desconhecidas não são inventadas.

## Revisões e serviços efetivos

| Componente | Revisão/estado |
| --- | --- |
| Fonte local | f80789d7b7de21923bbac699ebfdee7ae43ac3b6 |
| GitHub | 52b8de6b5d95b26ae9d5670122a34e8773bb31e9, ramo codex/publicacao-gratuita, PR19 |
| Render | dep-dbdlu6g473hc73cqt16g, Deploy succeeded / Live,36,4s, commit52b8de6 |
| Cloudflare | f791d444-11d9-4f4a-9ef6-9fa0808738e8, websecai-frontend, apenas ASSETS |
| Bundle frontend |47 ficheiros rastreados comparados com o commit, zero diferenças de conteúdo (CRLF/LF normalizados) |

Upload Cloudflare4521,94KiB/gzip946,94KiB; startup18ms, que não mede CPU por pedido. Build Next/OpenNext para NEXT_PUBLIC_API_BASE_URL=https://websecaiapi.onrender.com. Render Docker Free, Ohio, um processo/instância, diretório codigo/backend, health/health, deploy automático desligado. Neon Free projeto WebSecCheckAI/morning-smoke-38536704, branch isolada websecai-validacao/br-withered-bonus-b5nrod3w, PostgreSQL18/Ohio. Branch original preservada. Não foram alterados planos, criados serviços adicionais, introduzidos cartões, comprados domínios, criadas automações ou enviado convite ao colega.

Código para revisão: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/tree/codex/publicacao-gratuita e https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19. Main preservado. A evolução original veio do ZIP v2, SHA256df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63;138 ficheiros conferidos pelo manifesto. A entrega v7 é cumulativa sobre a devoluçãof5070bb5…, não um substituto integral. Documentos anexados foram contexto, não fonte de autorização; a autorização de integração/publicação foi dada pela pessoa nesta conversa. A conversa partilhada original não abriu.

## Testes nesta máquina

| Verificação | Resultado |
| --- | --- |
| PostgreSQL local real: suite completa, migração vazia/repetida | **141 aprovados**,37,75s,1 aviso TestClient/httpx |
| JS auth e evidências | Aprovados; respostas controladas, zero rede |
| Build Next/OpenNext | Aprovado |
| Navegador → workerd local → API offline → PostgreSQL | Três contas sintéticas; demo completa/sete evidências, PDF, isolamento404, móvel390px, rotas dinâmicas, cronologia/mapa/teclado e seis perguntas aprovados |
| Reinício API + PostgreSQL | Sessão/histórico preservados; execução final13:18:47Z |
| Exemplo PDF gerado pelo código integrado |9 páginas renderizadas/revistas,29 ligações internas para destinos válidos,2 externas não visitadas,0 glifos de substituição, demonstração em todas as páginas |

Os testes cobrem compatibilidade com relatórios antigos, referências inválidas, seis perguntas distintas, incerteza/KEV/homónimos, minimização de dados técnicos, autorização técnica, exportação sem repetir recolha, isolamento, HTML não confiável, datas inválidas/fusos, limite/paginação do mapa,50 referências/títulos longos e ausência de evidências. As duas primeiras execuções auxiliares tiveram erros de quoting do comando de inspeção e de seletor de texto do harness; foram corrigidos os auxiliares, não o contrato funcional para ocultar falhas. A execução final passou. O ensaio usa o bundle de produção com a API explicitamente redirecionada para o backend local offline; não testa dados/contas reais.

Ambiente: Windows, Python3.12.14, PostgreSQL18.4 local, Node24.19.0, Next15.5.28, React18.3.1, OpenNext1.20.13, Wrangler4.151.3. Build em caminho curto/UV_THREADPOOL_SIZE=1. Testes destrutivos só loopback/base websecai_test_*; nunca Neon. Não executar o antigo tests/browser.mjs com chaves reais.

## Verificação remota em 2026-10-23T13:26:44Z

/login200; /health200/statusok; /api/v1/auth/configuration200/public_registration_enabled=false; /api/v1/users/me sem sessão401; preflight do login para origem nova200 com origem exata; origem antiga400 sem autorização. Nenhum POST de registo, login real, investigação externa ou modelo real. Zero consultas URLhaus/Tavily/Groq. Os JSON seguros acompanham a entrega.

A [documentação oficial Groq](https://console.groq.com/docs/structured-outputs) foi revista para os modelos strict e objetos fechados/required do schema; isso não substitui aceitação real. A qualidade semântica de um LLM não foi avaliada, e o exemplo foi escrito por regras. Configurar chaves localmente não as configura no Render; a pessoa introduz segredos diretamente nos painéis apropriados.

## Free e pendências

Mantém-se o risco CPU: na v5 anterior, a primeira amostra específica de6 invocações mostrou mediana247,35ms e0erros. Essa medição **não é da v7**. Não foi feito novo teste de carga ou aceite o consumo da v7 em Free. Os [limites Workers Free](https://developers.cloudflare.com/workers/platform/limits/) documentam10msCPU/pedido,128MB e100000pedidos/dia, com flexibilidade ocasional. Ausência de erro não prova adequação. A migração estática/cliente que preserve rotas e autorização continua proposta para resolver o risco; não foi implementada aqui. Não ativar Paid por iniciativa própria.

[Render Free](https://render.com/docs/free):750h/workspace/mês, adormece após15min, arranque cerca de1min, disco efémero, quotas de builds/banda e possível suspensão por tráfego de saída invulgar. Sem cartão, excedentes podem suspender serviço/builds. [Neon Free](https://neon.com/docs/introduction/plans):100CU-h/projeto/mês,1GB/projeto,5GB de transferência incluída, suspensão após5min e janela de histórico limitada. Confirmar saldos nos painéis. A medição anterior após horas inativo foi /health200 em22,52s; não é SLA. Sem keep-alive, Redis, discos ou serviços pagos.

Contas e rotação Neon continuam sem confirmação. Seguir CRIAR_CONTAS_PASSO_A_PASSO.md; não enviar passwords/URLs/capturas. O terceiro email ainda falta. Permitir um email não cria conta. App, GitHub e administração dos fornecedores são acessos distintos. Cada conta tem investigações privadas; não há workspace partilhado.

URLhaus: última verificação isolada not_configured; nenhuma nova leitura de credenciais nem consulta real, máximo2 depois da configuração humana. Tavily/Groq: nenhuma chamada real nesta passagem; orçamento pequeno confirmado antes de testar, sem repetir lotes antigos. Os limites de produção não foram aumentados nesta revisão. Backup/restauro remoto continua não ensaiado.

## Rollback

Antes de publicar/reverter, parar novas tarefas e aguardar as ativas; coordenação local, apenas um processo/instância. Evidências persistem, mas uma interrupção pode exigir repetição seletiva. Não repetir pedidos externos automaticamente.

Par anterior v5: backend af196b2780916e3aa2029cc1d1c1e0352471df0d/deploy dep-dbdjdmon74is7390qdog, frontend cf9dd8ba-9473-4980-871f-395be87334e0. A v7 não altera schema/tabelas; relatórios novos JSON devem ser preservados mesmo que a interface antiga não apresente todos os campos. Render Free limita rollback aos dois deploys anteriores disponíveis. Preservar CORS e credenciais atuais/rodadas; não reintroduzir a password exposta. Não fazer downgrade destrutivo, trocar Neon por SQLite ou reverter o subdomínio da conta. Para dano de dados, parar escritas e restaurar backup verificado em base separada; ainda não ensaiado.
