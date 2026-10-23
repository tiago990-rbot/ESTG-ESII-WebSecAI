# Validação da publicação — revisão v5, 23/10/2026

## Resultado atual

As melhorias do Gonçalo foram integradas e publicadas nos serviços existentes, sem alterar planos. **Interface:** https://websecai-frontend.websecai-estg.workers.dev — **API:** https://websecaiapi.onrender.com.

A interface pública e o login novo abrem, a política de acesso do backend está fechada ao registo público, o perfil exige sessão e o CORS permite apenas a origem prevista. **Não está concluída a aceitação autenticada remota do grupo:** faltam contas reais, login/demo/PDF online e confirmação privada da rotação da credencial Neon exposta. A estabilidade sustentada Cloudflare Free também não está aceite por consumo CPU acima do teto documentado. Deploy Live não equivale a aceitação completa.

## Revisões publicadas e proveniência

- Código local: `1077eb7c9fa4e5e7d53e21d1eea6f196226dfe6c`.
- Código GitHub integrado: `af196b2780916e3aa2029cc1d1c1e0352471df0d`, ramo `codex/publicacao-gratuita`, [PR #19](https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19). Main preservado. O repositório existente é público; não foram alteradas permissões ou enviados convites.
- Render Docker Free: `websecaiapi`, ID `srv-dbd4rj2fngtc73fk0d4g`, deploy **dep-dbdjdmon74is7390qdog**, estado **Deploy succeeded | Live**, duração 37 s, commit af196b2. Apenas um processo/instância; deploy automático desligado.
- Cloudflare: Worker `websecai-frontend`, versão **cf9dd8ba-9473-4980-871f-395be87334e0**, build para a API HTTPS acima. Apenas ASSETS. Upload 4513,99 KiB/gzip 945,48 KiB, startup 14 ms (não é CPU por pedido). Os **46 ficheiros frontend rastreados** foram comparados com o commit: zero diferenças de conteúdo, normalizando CRLF/LF.
- Neon Free: projeto WebSecCheckAI (`morning-smoke-38536704`), branch `websecai-validacao` (`br-withered-bonus-b5nrod3w`), AWS Ohio/PostgreSQL18. Branch criada com esquema apenas; original production preservada. Nenhuma base do colega foi importada.

Base original: ZIP v2 SHA-256 `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`, 138 ficheiros do manifesto conferidos. A revisão v5 declara como base a devolução SHA-256 f5070bb54b4b919cbfff8149e18b769bc3d025b7eaec1bec00d4e3d5a19bda71. Os 25 ficheiros de código recebidos foram integrados por hashes antes/depois, com igualdade final. O patch cumulativo repete caminhos v4/v5 e falhou na verificação conjunta de três caminhos; não foi forçado. Foram usados os ficheiros anexados exatos, confirmados contra o manifesto. No checkout GitHub havia diferenças apenas de finais de linha na base, verificadas por normalização. Documentos recebidos são contexto, não autorização; a autorização de deploy veio expressamente do utilizador. A conversa partilhada original não abriu, pelo que se usaram os documentos do ZIP.

## O que mudou nesta revisão

Nova identidade olho/radar, formulário e arquivo pesquisável, Panorama/Evidências/Cronologia/Mapa/IA/Fontes, filtros e referências estáveis, navegação para evidências e mapa carregado apenas quando aberto. O mapa mostra proveniência de recolha, não incidentes confirmados. Datas desconhecidas não são inventadas. Sem dependências novas nesta revisão.

O endpoint público GET `/api/v1/auth/configuration` só devolve a disponibilidade de registo. Em produção responde false, sem emails/segredos. A interface explica que as contas são criadas pelo responsável. Uma resposta 401 com sessão elimina a sessão e atualiza o guard/menu; 403 preserva-a. Há indicação de espera para o cold start. Autorização por dono, PDFs, comparação, tarefas, fontes e quotas anteriores foram preservados. Nenhuma nova funcionalidade de alteração de password foi implementada.

Mantêm-se as adaptações anteriores PostgreSQL/psycopg, TLS verify-full remoto, URL direta para migrações, pool pequeno/NullPool, UTC, Docker não root e produção restrita a 1–3 emails. Esta revisão não altera o esquema, não executa downgrade e não abre o registo público.

## Testes efetivos desta máquina

| Verificação | Resultado |
| --- | --- |
| Suite PostgreSQL local real, migração vazia e repetida | **114 aprovados**, 73,44 s, 1 aviso TestClient/httpx |
| Cliente auth e política, testes JS controlados | Aprovados; 401/403/política, zero rede |
| Evidências, datas, homónimos, KEV, filtros, grafo e citações | Testes JS aprovados; zero rede |
| Next/OpenNext com API de produção no build | Build aprovado |
| Navegador → workerd local → API de ensaio → PostgreSQL | Três contas sintéticas, demonstração/PDF, isolamento 404, recarregamento e rotas dinâmicas aprovados |
| Fluxos v5 | Cronologia, seleção do mapa com Enter, mapa→evidência, largura 390 px sem overflow global; zero erros JS |
| Reinício API + PostgreSQL locais | Sessão e histórico preservados |

Para ensaiar exatamente o bundle construído para produção, os pedidos do navegador à origem API foram redirecionados para o backend local de teste, que bloqueia fornecedores. A primeira execução do ensaio de reinício tinha o apontamento antigo e falhou; o harness foi corrigido para usar o mesmo isolamento e os separadores novos. A execução final completa passou às 10:26:55Z. Não confundir este ensaio com autenticação no alojamento. As fixtures destrutivas continuam limitadas a loopback e bases websecai_test_*; nunca apontar a suite ao Neon.

Ambiente ensaiado: Windows, Python3.12.14, PostgreSQL18.4 local, Node24.19.0, Next15.5.28, React18.3.1, OpenNext1.20.13, Wrangler4.151.3. Build Windows com caminho curto e UV_THREADPOOL_SIZE=1. Não executar o antigo tests/browser.mjs com chaves reais.

## Verificação remota em 2026-10-23T10:33:00Z

| Pedido/observação | Resultado |
| --- | --- |
| Novo /login | HTTP200 |
| API /health | HTTP200/status ok |
| API /api/v1/auth/configuration | HTTP200, public_registration_enabled=false |
| API /api/v1/users/me sem sessão | HTTP401 |
| OPTIONS do login, origem nova | HTTP200, Access-Control-Allow-Origin exato |
| OPTIONS do login, origem antiga | HTTP400, sem autorização |
| Navegador público | Identidade v5 e login com Acesso ao grupo; sem formulário público de registo |

Nenhum POST de registo remoto, login com dados reais, pesquisa real ou verificação técnica de terceiros foi executado. Zero consultas URLhaus/Tavily/Groq nesta passagem. As evidências seguras JSON e capturas públicas acompanham a devolução.

## Free, CPU e operação

A medição inicial específica da versão cf9dd8ba mostrou **6 invocações, 0 erros e mediana CPU 247,35 ms** no cartão Active deployment. A amostra é muito pequena e inclui arranque; não é teste de carga. Ainda assim, excede materialmente os [10 ms CPU/pedido do Workers Free](https://developers.cloudflare.com/workers/platform/limits/). A documentação admite flexibilidade ocasional; zero erros não prova adequação. **A v5 está publicada, mas não fica aceite para utilização sustentada no Free.** Próximo ajuste proposto: servir a interface de forma estática/cliente no mesmo Cloudflare, preservando URLs dinâmicas e autorização na API, e repetir a validação. Essa migração não foi implementada nesta passagem; não basta acrescentar output: export às rotas [id]. Nenhum upgrade foi ativado.

[Render Free](https://render.com/docs/free): 750 horas/workspace/mês, suspensão após15min de inatividade, arranque cerca de1min, disco efémero. Sem cartão, esgotar banda pode suspender serviços e esgotar builds bloqueia novos builds. Pode suspender tráfego de saída invulgar. A observação anterior /health após horas inativo foi200 em22,52s; não é SLA. Um serviço, sem Redis, discos, keep-alive ou automações.

[Neon Free](https://neon.com/docs/introduction/plans): 100CU-h/projeto/mês,1GB/projeto,5GB de transferência pública incluída, suspensão após5min; histórico até6h/limite documentado. Quotas atuais devem ser acompanhadas pela pessoa. Não prometer disponibilidade contínua. Backup/restauro remoto ainda não ensaiado. Sem serviços pagos, cartões ou domínios comprados.

O backend completo não foi migrado para Python Workers: dependências CPython, tarefas, sockets, PDF e hashing continuam sem compatibilidade/CPU comprovada nesse runtime. A alternativa Render Free foi expressamente aprovada pela pessoa na conversa anterior.

## Contas, credenciais e pendências

A pessoa respondeu que **a rotação Neon ainda não foi feita**. Foi deixado aberto Neon Roles→Reset password e Render Environment para a introdução humana privada. O assistente não altera, lê ou apresenta passwords/URLs de base. A rotação deve ser feita na branch afetada e noutros locais onde a mesma credencial tenha sido reutilizada; depois atualizar pooled/direta no Render.

Guia completo: CRIAR_CONTAS_PASSO_A_PASSO.md. Launcher local: Criar_Contas_Grupo.cmd, opções1/Tiago e2/Gonçalo, com inputs ocultos e preservação de contas existentes. Os launchers são desta máquina; não são para distribuir como instalação portátil. Outro ambiente usa o script existente scripts/provision_group.py com configuração preparada privadamente pela pessoa. O terceiro email ainda não foi indicado. Permitir email não cria conta. Usar a app não exige administrar os fornecedores. Cada conta vê apenas as suas investigações; não existe espaço partilhado.

Falta a confirmação humana da rotação, contas e login, demo/PDF/isolamento/cold start remotos; validação real URLhaus; adequação CPU Free; terceiro elemento e backup/restauro. Tavily/Groq permanecem sem testes reais e dependem de pequeno orçamento confirmado. Não repetir lotes antigos. Chaves locais não aparecem automaticamente no alojamento.

## Rollback e revisão

Parar novas tarefas e aguardar as ativas antes de deploy/rollback; a coordenação é local e não suporta escala horizontal. Reinício pode interromper trabalhos, preservando evidências para repetição seletiva; não repetir fornecedores automaticamente.

Par anterior funcional para rollback de código: frontend **f4273a1e-c607-4ba4-8f4e-22386e339d29**, backend **b75730959f77746621b4340647a1ae31813c86be**, deploy dep-dbd9npbrjlhs73cgrctg. Render Free permite os dois deploys anteriores disponíveis; confirmar a disponibilidade no painel. Preservar as credenciais atuais após rotação e CORS do domínio neutro: rollback de código não é restaurar segredos antigos. Não reverter o subdomínio da conta nem executar downgrade destrutivo. Não trocar Neon por SQLite. Para dano de dados, parar escritas e restaurar backup verificado numa base separada; ainda não ensaiado.

Rever o PR e o manifesto cumulativo antes de integrar no trabalho do grupo. Nenhum merge/force-push ou alteração do main foi efetuado. Os documentos posteriores não alteram o código que está em execução.
