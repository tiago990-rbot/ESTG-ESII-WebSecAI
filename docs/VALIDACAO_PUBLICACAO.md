# Validação da publicação — 23/10/2026 (Portugal)

## CORS corrigido e confirmado — 2026-10-22T23:29:02.087594+00:00

Depois da correção humana e do deploy Render `dep-dbd9npbrjlhs73cgrctg`, a verificação remota confirmou: novo /login HTTP 200, API /health HTTP 200/status ok, preflight da origem nova HTTP 200 com a origem exata e origem antiga HTTP 400 sem autorização. O bloqueio CORS descrito nos registos anteriores está resolvido. Nenhuma credencial foi consultada e nenhuma chamada a fornecedores foi feita. Ainda faltam confirmar provisionamento, login e aceitação remota autenticada; o consumo CPU Cloudflare mantém-se pendente.

## Registo anterior, anterior à correção acima

## Resultado atual

A interface foi publicada em **https://websecai-frontend.websecai-estg.workers.dev** e a API em **https://websecaiapi.onrender.com**. A base persistente é PostgreSQL no Neon Free. **A aceitação online completa está pendente:** o novo endereço abre, mas a API ainda permite a origem antiga; faltam confirmar provisionamento/login individual, demonstração/PDF remotos e acesso dos colegas. Não declarar a instalação concluída só porque o deploy está Live.

A alteração de toda a conta Workers de tmelo1715.workers.dev para websecai-estg.workers.dev foi expressamente confirmada pela pessoa. O endereço anterior deixa de ser o endereço de utilização. A aplicação Pages existente atria-operations-teste.pages.dev foi preservada. É necessário iniciar sessão no novo endereço; a sessão de outra origem não é transferida.

## Evidência remota

| Verificação | Resultado |
| --- | --- |
| Novo `/login` | HTTP 200, 2026-10-22T23:09:52Z; também aberto no navegador |
| API `/health` | HTTP 200, status ok |
| API sem autenticação | 401 no ensaio remoto anterior |
| CORS novo endereço (ensaio anterior) | 400 antes da correção; **200 no ensaio final acima** |
| CORS endereço antigo (ensaio anterior) | 200 antes da correção; **400 no ensaio final acima** |
| Após horas de inatividade | `/health` 200 em 22,52 s às 22:27:17Z; uma observação, sem SLA |
| Rotas interface, antes da mudança do nome | `/`, `/login`, `/about`, `/history/[id]`, `/investigations/[id]` responderam 200, sem erro 1102; IDs fictícios, sem prova de acesso a dados |
| Login/demonstração/PDF dos utilizadores reais | Não confirmados |
| URLhaus/Tavily/Groq | Zero consultas reais durante esta passagem |

Evidências JSON seguras acompanham a devolução. GET e preflight OPTIONS só foram feitos na própria aplicação. Não foram visitados alvos maliciosos nem usadas verificações técnicas de terceiros.

## Correção humana pendente no Render

Em websecaiapi → Environment → Edit, guardar os seguintes valores públicos, sem alterar os restantes:

```text
CORS_ORIGINS=https://websecai-frontend.websecai-estg.workers.dev
APP_ALLOWED_EMAILS=<lista privada dos dois emails autorizados>
```

Escolher **Save, rebuild, and deploy** e guardar. O assistente submeteu estes valores sem revelar campos, mas o comportamento remoto continuou antigo. A revisão automática bloqueou a opção Show secret, incluindo nos campos públicos; não foram lidos valores de credenciais nem tentada extração de segredos. A pessoa precisa de concluir a edição no painel. Após Live, repetir OPTIONS: novo endereço deve obter 200 e origem exata; antigo e origem desconhecida devem ser recusados. Não testar isto criando contas públicas.

Gonçalo foi solicitado na configuração; **permitir um email não cria uma conta** e ainda falta comprovar a configuração efetiva. Registo público é fechado pelo backend de produção, embora a interface recebida continue a mostrar Criar conta. Usar provisionamento privado e login, conforme PASSOS_DA_PESSOA.md. O terceiro email ainda não foi identificado. Cada conta mantém as suas investigações; não foi criado um espaço partilhado.

## Serviços, revisão online e planos

- Neon: projeto WebSecCheckAI (`morning-smoke-38536704`), branch isolada `websecai-validacao` (`br-withered-bonus-b5nrod3w`), criada com esquema apenas, sem dados do colega. Ramo original preservado. AWS Ohio/PostgreSQL 18; painel Free $0. Ligações pooled/direta foram introduzidas pela pessoa.
- Render: serviço `websecaiapi`, ID `srv-dbd4rj2fngtc73fk0d4g`, Docker Free, Ohio, root `codigo/backend`, uma instância, health `/health`, deploy automático desligado. Último deploy Live observado: `dep-dbd9at1srm7s73auivng`, revisão `51fb12ef0a4b4b4958463e86dcfa55e83367d99a`. Após tentativas de CORS foi solicitado um reinício; sem prova de alteração do CORS. Builds Docker reais passaram. Os dois deploys iniciais falharam por URLs de base inválidas; a pessoa corrigiu-as e o arranque/migração passou.
- Cloudflare: Worker `websecai-frontend`, versão atual `f4273a1e-c607-4ba4-8f4e-22386e339d29`, bundle equivalente à versão anterior `320d69d3-2b44-4571-adc1-c93bb0eca922`, agora no subdomínio neutro. Apenas ASSETS; sem R2/KV/D1/serviços pagos. Build `NEXT_PUBLIC_API_BASE_URL=https://websecaiapi.onrender.com`. Os 36 ficheiros frontend rastreados foram comparados com o código integrado: zero diferenças. Upload 4149,60 KiB, gzip 853,37 KiB; startup 16 ms não é CPU por pedido.
- Código: [ramo de publicação](https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/tree/codex/publicacao-gratuita), [PR #19 em rascunho](https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19). Código integrado `8b9707ae4c95ea321f6f782cb01df179e61fcb94`; `51fb12e` só acrescentou documentação. Relatórios posteriores não alteram o código executado. O main e README inicial foram preservados. O repositório existente é público; não foi alterada a sua visibilidade.

## Quotas e limitação concreta Cloudflare

Condições oficiais consultadas em 22/10/2026 UTC:

- [Workers Free](https://developers.cloudflare.com/workers/platform/limits/): 100 000 pedidos/dia, 10 ms CPU/pedido, 128 MB. O painel, para as primeiras 11 invocações da versão anterior do mesmo bundle, mostrou **P50 CPU 18,322 ms, P90 122,736 ms e P99 374,823 ms**, zero erros Exceeded CPU Time Limits. A documentação admite flexibilidade ocasional; **zero erros não prova adequação aos limites**. A interface está acessível, mas o bundle Next/OpenNext não fica aceite para utilização sustentada em Free com estas medições. Próxima opção sem novos serviços: reduzir renderização no Worker e preparar entrega estática/cliente no mesmo Cloudflare Free, preservando rotas e autorização da API; exige implementação e testes próprios antes de substituir a versão atual. Não ativar Workers Paid nem aumentar limites pagos. Não foi feito teste de carga nem prometida capacidade para três utilizações simultâneas.
- [Render Free](https://render.com/docs/free): 750 horas/workspace/mês, partilhadas; adormece após 15 minutos, arranque em cerca de um minuto, disco efémero. Sem meio de pagamento, banda esgotada suspende serviços e minutos de build esgotados impedem builds. Pode haver suspensão por volume invulgar de tráfego iniciado pelo serviço. Sem keep-alive, discos ou Redis. O fornecedor enquadra Free para testes/projetos pessoais, sem disponibilidade de produção garantida.
- [Neon Free](https://neon.com/docs/introduction/plans): 100 CU-h/projeto/mês, 1 GB/projeto, 5 GB de transferência pública incluída, suspensão após cinco minutos. Histórico até seis horas/limite documentado de 1 GB-month. Backup/restauro remoto ainda não testado.

Zero euros: não foram contratados planos pagos, introduzidos cartões, comprados domínios nem criadas automações. Nenhum saldo de quota foi presumido como garantia futura. Parar ao atingir limites.

## Adaptações e testes de código

A base foi o ZIP v2, SHA-256 `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`. Manifesto original preservado, 138 ficheiros verificados sem diferenças. A conversa partilhada não abriu; foram usados os documentos do ZIP.

Revisão local `8d8cf77199ee0bfc31b4bd5ac610a8c55a524053`, base local `8a83f2d`: 33 ficheiros de código alterados/adicionados, discriminados no manifesto e patch.

PostgreSQL psycopg3, TLS verify-full/certifi remoto, ligação direta separada para migrações, rejeição de pooler/destino divergente, pool 2+2/NullPool migração, prepared statements automáticos desligados. Normalização UTC. Produção exige PostgreSQL, CORS HTTPS e 1–3 emails autorizados; registo público fechado e autorização por dono preservada. Parser aceita URL ou snippet psql estritamente analisado, sem executar comandos nem revelar ligação. Um processo FastAPI; recuperação de tarefas e repetição seletiva preservadas. Docker não root. Não foram implementados passwords novas/alteração de password, redesign, grafos ou partilha de investigações.

| Teste executado nesta máquina | Resultado |
| --- | --- |
| Suite original | 98 aprovados |
| Após primeira adaptação SQLite/PostgreSQL | 105 aprovados + 1 omitido / 106 aprovados |
| Revisão final PostgreSQL local real | **113 aprovados**, migração inicial e repetição idempotente |
| Casos finais SQLite deployment/security | 15 aprovados, 1 omitido |
| Navegador → workerd → FastAPI → PostgreSQL | Três contas sintéticas, demo com quatro evidências fictícias, PDF, isolamento 404, histórico/rotas dinâmicas, móvel 390 px, zero erros JS/pedidos externos |
| Reinício API e PostgreSQL locais | Sessão e histórico preservados |
| Build Next/OpenNext e deploy real Cloudflare | Aprovados; limitação CPU acima discriminada |

Ambiente: Windows, Python 3.12.14, Node 24.19.0/npm 12.2.1, PostgreSQL 18.4 local, psycopg 3.3.6, SQLAlchemy 2.1.5, Alembic 1.20.0, Next 15.5.28, React 18.3.1, OpenNext 1.20.13, Wrangler 4.151.3. Build Windows com caminho curto e UV_THREADPOOL_SIZE=1, por EPERM; WSL/Linux pode ser necessário noutra máquina. Testes de fornecedores são controlados, não aceitação real.

## Aceitação e rollback

Depois de corrigir CORS e criar contas privadamente, cada pessoa deve entrar no mesmo link e testar apenas a demonstração: conclusão da tarefa, histórico, PDF, recarregamento, comparação e isolamento. Guardar resultado UTC, sem passwords/tokens. Não executar a suite destrutiva PostgreSQL contra o Neon: só aceita loopback e websecai_test_*. Não executar o antigo tests/browser.mjs num ambiente com chaves. Um POST de registo remoto de ensaio foi bloqueado por revisão automática e não foi executado; não existe prova desse teste nem deve ser repetido como alternativa ao provisionamento.

Antes de deploy/rollback, impedir novas tarefas e aguardar pelas atuais: coordenação local, apenas um processo/instância. Reinício pode interromper tarefas; evidências persistem e a recuperação permite repetição seletiva, sem repetição externa automática garantida. Não escalar horizontalmente.

Rollback da interface: versão anterior 320d69d3, verificando o novo domínio/CORS. Não reverter o subdomínio da conta sem nova decisão. Backend: escolher revisão PostgreSQL compatível; Render Free limita rollback aos dois deploys anteriores disponíveis. Os deploys iniciais falhados não são recuperação válida. Guardar snapshot/backup privado e ensaiar restauro numa base separada antes de alterações de dados; não foram feitos nesta passagem. Não fazer downgrade destrutivo nem trocar Neon por SQLite. Se houver dano, parar escritas e restaurar cópia verificada. Nenhum dump/segredo acompanha a entrega.
