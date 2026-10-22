# Validação da publicação — 22/10/2026

## Estado real

**Código enviado para o GitHub; testes locais concluídos; aplicação ainda não publicada.** Conta GitHub `tiago990-rbot` confirmada pela CLI. A revisão de integração `e926bd4a323b68978475a83bf8cc797cd1c5c690` está no [ramo autorizado](https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/tree/codex/publicacao-gratuita), com [PR #19 em rascunho](https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19). A árvore de ficheiros e o commit remotos coincidem com o snapshot local; não houve force-push nem alteração de main.

Neon `WebSecCheckAI` (`morning-smoke-38536704`), AWS Ohio: plano **Free / $0** confirmado. Foi criada a branch **websecai-validacao** (`br-withered-bonus-b5nrod3w`), com esquema apenas, sem copiar dados do ramo original e sem expiração automática. A branch original `production` foi preservada. Não foram lidas ligações privadas nem feitas migrações ou testes remotos.

Cloudflare: conta com subdomínio `tmelo1715.workers.dev` confirmada; a aplicação existente foi preservada. Nenhum Worker WebSecAI publicado. Render: `Tiago's workspace`, formulário de um único serviço `websecai-api` preparado com **Free / $0**, 0.1 CPU, 512 MB RAM, Ohio, Docker, ramo `codex/publicacao-gratuita`, pasta `codigo/backend`, contexto `.`, Dockerfile `./Dockerfile`, health `/health`, deploy automático **Off**. O formulário inicial foi depois submetido pela pessoa; o serviço criado e o primeiro erro estão registados na atualização abaixo. Não foram ativados planos pagos, meios de pagamento, domínios, extras ou automações.

| Componente | Comprovado | Ainda pendente |
| --- | --- | --- |
| FastAPI/SQLite local | Instalação e regressão | — |
| PostgreSQL | Migrações e suite locais; branch Neon Free isolada criada | TLS remoto, pooler, migrações e aceitação reais |
| Interface Cloudflare | Bundle OpenNext e navegador no workerd local | Deploy Free, limites e métricas reais |
| Backend Cloudflare Python | Documentação e análise de compatibilidade | Nenhum teste de runtime/implantação completo |
| Backend CPython tradicional | API local com PostgreSQL | Execução no Render, Docker Linux e cold start remoto |
| URLhaus | Configuração ausente; testes controlados | Autenticação real |

URL público da interface: **não existe ainda**. URL atribuído à API: **https://websecaiapi.onrender.com**, ainda sem arranque validado. Os endereços `http://127.0.0.1:3000` e `http://127.0.0.1:8000` foram usados apenas durante os testes e os processos de teste foram encerrados. Nomes futuros `*.workers.dev`/`*.onrender.com` dependem das contas e disponibilidade; não são URLs publicados.

## Atualização após o primeiro deploy Render

O serviço **websecaiapi** foi criado pela pessoa no Render Free, ID `srv-dbd4rj2fngtc73fk0d4g`, no ramo de publicação. Endereço atribuído: https://websecaiapi.onrender.com . O primeiro deploy `dep-dbd4rjafngtc73fk0eng`, revisão `922e0c4`, falhou no arranque com a mensagem segura «URL da base inválida». Ter um endereço atribuído não prova que a API esteja operacional. Não foram lidas ligações, chaves ou passwords nos campos privados.

A pessoa pediu acesso inicial só com a sua conta. A lista de acesso no Render foi atualizada com o email indicado; o endereço pessoal não é reproduzido neste relatório público. O backend aceita agora **entre um e três emails autorizados**, recusando lista vazia ou acima de três. Registo público e acesso de não membros continuam bloqueados. O provisionamento percorre apenas os emails configurados; os restantes elementos podem ser acrescentados depois.

A leitura da ligação aceita também aspas exteriores ou o snippet `psql 'URL'` fornecido pelo painel Neon. É apenas análise de texto, sem executar comandos. Opções adicionais/snippets inválidos são recusados sem expor valores; TLS e a correspondência entre pooler e ligação direta mantêm-se. Isto cobre uma causa possível do erro de formato; o resultado remoto ainda precisa de ser comprovado.

Código local atualizado: `8d8cf77199ee0bfc31b4bd5ac610a8c55a524053`. Testes focados: **15 aprovados e 1 omitido** em SQLite. Suite PostgreSQL real repetida após estas alterações: **113 aprovados**, incluindo migração inicial/idempotência. Não houve chamadas reais URLhaus/Tavily/Groq. Nova publicação e teste de saúde remotos pendentes.

## Revisão e proveniência

- Base: ZIP `WebSecAI_Continuacao_2026-10-22_v2.zip`, SHA-256 `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`.
- `MANIFEST_SHA256.json` original preservado, SHA-256 `c2d35dec720e28ac1737b01b498a1c79032c54aef2067cb10bf57c4688ede490`. Os 138 ficheiros corresponderam ao manifesto.
- Commit-base local: `8a83f2d`; revisão preparada: `38b3c378ee1ad002850e1a2bf5cb7843ab0b2252`.
- Ramo remoto: `codex/publicacao-gratuita`, integração `e926bd4a323b68978475a83bf8cc797cd1c5c690`, PR #19. Código enviado com a API oficial GitHub através da CLI autenticada, sem ler tokens. A conversa partilhada não abriu; os documentos do pacote forneceram o contexto.
- Ambiente efetivo: Windows, Python 3.12.14, Node 24.19.0, npm 12.2.1, PostgreSQL 18.4 local (binários de teste `@embedded-postgres/windows-x64` 18.4.0-beta.17), psycopg 3.3.6, SQLAlchemy 2.1.5, Alembic 1.20.0, Next.js 15.5.28, React 18.3.1, OpenNext Cloudflare 1.20.13, Wrangler 4.151.3/workerd 1.20261019.1.

## Alterações preparadas

1. Driver psycopg 3 fixado. Aceita `postgres://`, `postgresql://` e `postgresql+psycopg://`, preservando SQLite local.
2. PostgreSQL remoto exige TLS com verificação de certificado/hostname (`verify-full`, CA do certifi). Ligações `require` são reforçadas; modos inseguros são recusados. A exceção sem TLS serve apenas PostgreSQL em loopback nos testes.
3. `DATABASE_URL` para aplicação e `DATABASE_MIGRATION_URL` direta para Alembic. Migrações recusam endpoint `-pooler` e destino diferente. Pool pequeno (2 + até 2 ligações adicionais), pre-ping e prepared statements automáticos desativados para o pooler. Alembic usa NullPool.
4. Datas lidas da base normalizadas para UTC sem alterar os tipos SQL existentes. O teste inicial detetou o fuso da sessão PostgreSQL; a correção foi verificada.
5. `APP_ENV=production` exige PostgreSQL, entre um e três emails em `APP_ALLOWED_EMAILS` e CORS HTTPS explícito. Registo público fechado; login e autorização continuam individuais. Utilizadores fora da lista não entram, mesmo com sessão antiga. Limite de tentativas por IP/identificador no processo.
6. `scripts/provision_group.py` prepara as contas através de terminal humano com palavra-passe oculta e configuração privada `.env.production`. Preserva contas existentes. O assistente não o executou nem conhece credenciais. Não foi criada uma funcionalidade nova de alteração de password.
7. Entrada CPython `scripts/start_hosted.py` com um worker; Dockerfile e `render.yaml` preparados, sem segredos. O YAML define apenas um serviço Free e desativa deploys automáticos; sintaxe/caminhos/condições locais verificados. A validação Render remota ainda não foi feita. Docker/Linux ainda não executado nesta máquina. O exemplo Render usa Ohio para ficar na região do projeto Neon identificado; confirmar essa escolha no painel antes da criação.
8. OpenNext e Wrangler fixados, scripts de build/preview/deploy e configuração sem bindings adicionais. Mantidas as rotas dinâmicas; não foi usado `output: export`. O build exige URL pública da API; localhost só com preview explícito.

Não foram implementados redesign, grafos ou partilha entre contas. A revisão mantém PDFs, Threat Intelligence, autorização por dono, histórico, comparação e repetição seletiva.

## Evidência dos testes

| Verificação | Resultado efetivo |
| --- | --- |
| Suite original sem alterações | 98 aprovados |
| Build Next.js original | Aprovado |
| Suite após adaptação em SQLite | 105 aprovados, 1 omitido por exigir PostgreSQL |
| Migração PostgreSQL numa base vazia | Aprovada; repetida sem perda de dados |
| Suite em PostgreSQL local | 106 aprovados |
| Casos novos | JSON, datas UTC, IDs, cascatas, isolamento e reservas de quota concorrentes |
| Regressão existente | PDFs, autenticação, tarefas, recuperação, comparação, repetição de fontes e TI com respostas controladas |
| Guarda adicional do destino de migração | Teste focado aprovado após a revisão final |
| Bundle OpenNext | Gerado com sucesso |
| Chrome → workerd local → FastAPI → PostgreSQL | Aprovado para três contas sintéticas |
| Reinício local da API e PostgreSQL | Sessão e histórico preservados; aprovado no navegador |
| Aceitação dos três colegas em máquinas distintas | Não realizada |
| Neon/Render/Cloudflare remotos | Não realizados |

O teste de navegador no runtime Cloudflare local terminou em `2026-10-22T13:15:36.272Z`: demonstração com quatro evidências fictícias, PDF, conta sem acesso aos dossiês alheios, rotas `/investigations/[id]` e `/history/[id]`, recarregamento e largura móvel de 390 px. Zero erros JavaScript e zero pedidos externos do navegador. O teste usa backend isolado sem chaves e CISA controlada; não é pesquisa real nem avaliação de modelo.

O teste após reinício terminou em `2026-10-22T13:15:43.829Z`. As provas locais não demonstram limites de CPU, TLS remoto, disponibilidade ou cold start no alojamento.

Há um aviso de descontinuação FastAPI/Starlette relativo ao TestClient/httpx. Não causou falhas. O adaptador OpenNext avisa que Windows não tem compatibilidade completa. Encontraram-se erros EPERM na cópia standalone; o build passou com caminho mais curto e `UV_THREADPOOL_SIZE=1`, agora definido pelo script de build. WSL/Linux continua a ser uma opção se outra máquina tiver esse problema. Não houve alteração de versão principal do Next.js.

## Backend Cloudflare e alternativa proposta

A [Cloudflare documenta FastAPI em Python Workers](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/). Isso não prova que esta API CPython seja equivalente nesse ambiente. O código mantém requests síncronos, sockets/DNS, semáforos, BackgroundTasks, cache de ficheiros, SQLAlchemy/psycopg, PBKDF2 e ReportLab. Persistência de tarefas e dependências continuam sem prova em Python Workers.

O hash atual usa 600 000 iterações. Uma medição CPython local consumiu 375 ms de CPU; **não é uma medição em Workers**. Comparada com o teto Free de 10 ms, indica risco material. Não se reduziu o hash nem se declarou Python genericamente impossível na Cloudflare.

Arquitetura aprovada pela pessoa nesta conversa: **Cloudflare Workers Free para interface, Render Web Service Free para FastAPI e Neon Free para dados**. Mantém o processo Python convencional. O workspace Render foi identificado e o formulário Free preparado; o serviço ainda não foi criado. Se a pessoa preferir insistir no backend Workers, é necessária uma prova específica antes da publicação; o bundle frontend aprovado não resolve esse trabalho.

## Passos humanos e publicação, por ordem

1. Contas/projetos Neon/Cloudflare/Render, repositório e ramo já identificados e autorizados. Render Free para o backend já foi autorizado, sem cartão nem extras. Fazer logins pessoalmente; não enviar credenciais ao modelo.
2. Integração enviada para o ramo de publicação e PR #19. Revisão de código `e926bd4a323b68978475a83bf8cc797cd1c5c690`; código/helper comparados com o snapshot testado. O README inicial está em `docs/README_INICIAL_GITHUB.md`; main permanece intacto para revisão.
3. A branch isolada Neon Free `websecai-validacao` já foi criada com esquema apenas, separada do ramo original. Selecionar esta branch no painel Connect para a validação inicial. A pessoa guarda as URLs pooled/direta privadamente nos ambientes apropriados. Não importar a base pessoal do colega. Testar TLS/pooler/migrações e a demonstração nesse destino antes de usar a base final.
4. Com Render Free já autorizado: criar um único Web Service Free no repositório autorizado, diretório `codigo/backend`. Opção Docker com o Dockerfile fornecido; alternativa de runtime Python 3.12.14, build `pip install -r requirements.txt`, start `python scripts/start_hosted.py`. Confirmar Free antes de criar. Não criar Render Postgres, Redis, cron, disco pago ou worker adicional. A base persistente continua no Neon.
5. A própria pessoa configura no painel do backend `APP_ENV=production`, `APP_ALLOWED_EMAILS` (um email nesta etapa; até três quando o grupo estiver pronto), `DATABASE_URL` pooled, `DATABASE_MIGRATION_URL` direta, `JWT_SECRET` aleatório estável, `CORS_ORIGINS` com a origem HTTPS exata da interface e `ALLOW_DEMO=true`. Não copiar o `.env` para o repositório ou imagem. Manter `SEARCH_MONTHLY_LIMIT=0` e `AI_DAILY_LIMIT=0` enquanto não houver pequeno orçamento humano para testes externos. Chaves opcionais podem continuar ausentes.
6. Para provisionar as contas, a pessoa prepara `.env.production` privada em `codigo/backend` com a configuração do destino e executa `python scripts/provision_group.py` no seu terminal. As passwords são introduzidas por getpass. Não executar isto através do assistente nem enviar o ficheiro. A conta do docente/grupo no Neon não substitui as contas WebSecAI.
7. No projeto Cloudflare Free, usar o frontend e o adaptador fixados. Configurar `NEXT_PUBLIC_API_BASE_URL` no **ambiente de build** com a API HTTPS escolhida. Build `npm ci` seguido de `npm run build:cloudflare`; depois `npm run preview:cloudflare` antes do deploy. `npm run deploy:cloudflare` apenas na conta/projeto identificado. Usar `*.workers.dev`, sem domínio comprado. Não ativar R2, Containers ou produtos adicionais por rotina.
8. Atualizar CORS no backend para a origem real. Não colocar chaves ou URLs de base em `NEXT_PUBLIC_*`. O formulário Windows só configura a máquina local.
9. Fazer aceitação real em duas máquinas/navegadores, com as três contas: login, demonstração, acompanhamento, histórico, comparação, PDF, recarregamento e impossibilidade de consultar dossiês alheios. Verificar erros sem chave e repetir após cold start remoto. Repetição de fonte pode ser testada sem chave; chamadas reais Tavily/Groq só com orçamento pequeno confirmado, sem lotes antigos.
10. Registar aqui os URLs efetivos, commit em cada deploy, plano mostrado no painel, data, resultado dos três acessos e consumo. Se a conta pedir pagamento ou o runtime ultrapassar os limites, parar e voltar à decisão humana.

Os comandos da suite destrutiva PostgreSQL recusam destinos remotos: só aceitam loopback e nomes `websecai_test_*`. Não a apontar ao Neon. A validação remota deve usar uma base dedicada e os fluxos de aceitação sem limpeza destrutiva.

## Como os três entram

Depois de publicado e provisionado, cada elemento abre o mesmo URL HTTPS e usa o seu username/email e palavra-passe WebSecAI. O registo público fica fechado. Não precisam de partilhar uma sessão, ter permissões de administrador dos fornecedores ou manter um computador ligado. As investigações continuam privadas por dono. Um espaço de grupo exigiria definição e implementação próprias.

## Quotas, suspensão e custo

- [Neon Free](https://neon.com/pricing): 1 GB por projeto, 100 CU-h/projeto/mês, suspensão após cinco minutos de inatividade, sem cartão obrigatório. A página lista restauro limitado até seis horas ou 1 GB de alterações. Confirmar os valores no projeto escolhido.
- [Workers Free](https://developers.cloudflare.com/workers/platform/limits/): 100 000 pedidos/dia, 10 ms de CPU por pedido, 128 MB de memória. O tempo de parede do preview não mede essa quota de CPU. Validar métricas reais das rotas dinâmicas antes de declarar o frontend aceite em Free.
- [Render Free](https://render.com/docs/free): 750 horas por workspace/mês, partilhadas; suspensão ao esgotar as horas. Adormece após 15 minutos e pode demorar cerca de um minuto a arrancar. Disco local efémero. Sem método de pagamento, banda esgotada pode suspender serviços e minutos de build esgotados podem impedir novos builds. Confirmar os saldos de banda/build no workspace. Não adicionar cartão nem tráfego artificial de keep-alive.
- As quotas das fontes passam a ser partilhadas pelos três. Limites locais restringem utilização; não garantem custo nem substituem as condições das contas. URLhaus não tem quota numérica assumida neste relatório.

Sem SLA ou disponibilidade contínua prometida. Ao atingir limites, suspender/recusar utilização; não ativar upgrades. Não foram contratados serviços nem introduzidos meios de pagamento.

## Revisão online e rollback

Antes do primeiro deploy, comparar o patch/manifesto e registar o commit de integração no painel de cada alojamento. A interface e a API têm de apontar à mesma revisão compatível; registar URLs e IDs de deploy neste relatório. O código está acessível no GitHub no ramo/PR acima; ainda não há uma revisão da aplicação executada online. Alterações posteriores apenas aos relatórios não substituem os testes do código dessa revisão.

Para cada alteração futura, combinar uma janela com o grupo e aguardar pelo fim dos trabalhos antes de publicar. Um worker/instância CPython inicialmente; não escalar horizontalmente. O semáforo é local e a recuperação marca trabalhos globalmente, incluindo risco de sobreposição entre processos durante rollout. Uma interrupção preserva evidências e permite repetição seletiva; não garante conclusão nem deve repetir pedidos externos automaticamente.

Guardar backup/snapshot privado antes da migração e testar o restauro numa base separada; **backup e restauro remotos ainda não foram realizados**. Não incluir dumps no pacote. No rollback, repor o deploy frontend anterior e a última revisão de backend compatível com PostgreSQL. A base SQLite original não é um rollback pronto para uma app Neon. Não executar downgrade destrutivo: a migração herdada recusa-o. Se houver dano nos dados, parar escritas e restaurar uma cópia verificada dentro da janela disponível. Render Free só oferece rollback para os dois deploys anteriores indicados na documentação.
