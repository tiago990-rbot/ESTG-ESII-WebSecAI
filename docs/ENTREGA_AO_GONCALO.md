# Continuação WebSecAI — entrega ao Gonçalo

## CORS corrigido e confirmado — 2026-10-22T23:29:02.087594+00:00

Depois da correção humana e do deploy Render `dep-dbd9npbrjlhs73cgrctg`, a verificação remota confirmou: novo /login HTTP 200, API /health HTTP 200/status ok, preflight da origem nova HTTP 200 com a origem exata e origem antiga HTTP 400 sem autorização. O bloqueio CORS descrito nos registos anteriores está resolvido. Nenhuma credencial foi consultada e nenhuma chamada a fornecedores foi feita. Ainda faltam confirmar provisionamento, login e aceitação remota autenticada; o consumo CPU Cloudflare mantém-se pendente.

## Registo anterior, anterior à correção acima

## Para usar a aplicação

Link: **https://websecai-frontend.websecai-estg.workers.dev/login**. API: https://websecaiapi.onrender.com. O novo link abre, mas falta corrigir CORS no Render antes do login funcionar nesse endereço; seguir PASSOS_DA_PESSOA.md.

O email pedido para Gonçalo foi incluído na tentativa de configuração; a persistência efetiva e a criação da sua conta não foram comprovadas. Tiago deve guardar os dois valores públicos descritos no guia e provisionar a conta privadamente. Depois Gonçalo entra com username/email e password WebSecAI próprios. O botão público Criar conta não é o mecanismo de entrada em produção. Não precisa de credenciais Neon/Render/Cloudflare. As investigações permanecem privadas por dono.

## Código para continuar

- Repositório público existente: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI
- **Ramo com esta evolução: codex/publicacao-gratuita**. O main ainda não contém esta evolução.
- Revisão de código integrada: `8b9707ae4c95ea321f6f782cb01df179e61fcb94`. Commit do backend em execução: `51fb12ef0a4b4b4958463e86dcfa55e83367d99a` (acrescenta só documentação ao código referido).
- Revisão para o grupo: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19 (rascunho).
- Cloudflare: versão `f4273a1e-c607-4ba4-8f4e-22386e339d29`, mesmas fontes frontend comparadas com a revisão integrada.

Para uma cópia nova:

```powershell
git clone --branch codex/publicacao-gratuita https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI.git
cd ESTG-ESII-WebSecAI
git switch -c trabalho-goncalo
```

Para uma cópia do grupo já alterada, preservar primeiro dados e ficheiros privados e integrar por comparação/ramo; não substituir pela pasta toda. O pacote WebSecAI_devolucao_alteracoes.zip contém apenas 33 ficheiros de código alterados/adicionados, relatórios, evidências seguras, manifesto e patch. Exige a base do ZIP original v2 para aplicação direta. Seguir INTEGRACAO_DO_PATCH.md e começar por `git apply --check`.

Base recebida: WebSecAI_Continuacao_2026-10-22_v2.zip, SHA-256 `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`; 138 ficheiros do manifesto original conferidos. A evolução veio desse ZIP; não foi inferida a partir do GitHub. A conversa partilhada não abriu para o assistente. O README anterior do GitHub está preservado em docs/README_INICIAL_GITHUB.md.

## Instalação local para desenvolvimento

Versões ensaiadas: Python 3.12.14, Node 24.19.0, PostgreSQL 18.4. Em codigo/backend:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe scripts/setup_local.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Noutro terminal, em codigo/frontend:

```powershell
npm ci
npm run dev
```

Abrir http://localhost:3000. SQLite continua disponível localmente. setup_local cria configuração privada apenas se não existir. Não enviar .env ao assistente nem ao GitHub. A demonstração fictícia não precisa de Tavily/Groq; consultas reais de módulos são outra operação. Para testar PostgreSQL, usar exclusivamente uma base local dedicada `websecai_test_*`; as fixtures são destrutivas e recusam Neon.

## O que foi adaptado e testado

PostgreSQL/TLS/migrações diretas, UTC, controlo de membros em produção, registo público fechado, provisionamento privado, Docker/Render Free e Next/OpenNext/Cloudflare. Mantêm-se autenticação, autorização por dono, tarefas, PDFs, histórico, comparação, repetição seletiva e TI. Não foram implementados redesign, grafos, alteração de password ou espaço partilhado.

113 testes passaram em PostgreSQL local real. Navegador com três contas sintéticas passou demo/PDF/isolamento/reinício/rotas dinâmicas. Backend e interface foram publicados realmente; falta aceitação autenticada remota. Ler VALIDACAO_PUBLICACAO.md para evidências e limites. URLhaus: última verificação not_configured, zero consultas reais; testes positivos/no_results existentes são controlados. Não afirmar autenticação sem consulta oficial.

## Pendências e condições para continuar

1. Corrigir CORS e confirmar os emails no Render; criar contas privadamente e testar login/demo/PDF/isolamento/cold start online. Terceiro email ainda pendente.
2. CPU Cloudflare observado P50 18,322 ms/P99 374,823 ms acima do limite Free documentado de 10 ms. Zero erros até agora não prova estabilidade. Avaliar entrega estática/cliente no mesmo Free, preservando as rotas, antes de afirmar a publicação aceite. Não ativar plano pago por iniciativa própria.
3. URLhaus: a própria pessoa guarda a Auth-Key no formulário oculto local. No máximo duas tentativas totais ao fornecedor oficial nesta passagem; scripts/validar_urlhaus.py guarda reservas. Não apagar contadores, visitar URLs maliciosos ou chamar outros fornecedores para este teste. Configuração, autenticação e ausência de correspondências são estados distintos.
4. Tavily/Groq só com pequeno orçamento humano confirmado; nenhum teste externo feito. Os limites no alojamento foram preparados a zero. Configurar segredos diretamente nos painéis, por ambiente.
5. Confirmar terceiro elemento, revisão humana do PR e backup/restauro remoto numa base separada. Sem merge automático nem substituição da instalação do colega.

## Publicação e recuperação

Arquitetura autorizada a zero euros: Cloudflare Free/interface + Render Free/FastAPI + Neon Free/PostgreSQL. Render adormece aos 15 min e o primeiro acesso pode levar cerca de um minuto; Neon também suspende compute. Dados no Neon, não no disco efémero Render. Não manter portátil ligado para servir a app. Não criar keep-alive/automação, cartões, domínios pagos ou serviços adicionais.

Deploys são manuais. Antes de publicar, parar novas tarefas e esperar pelas ativas; apenas um processo/instância. Código/frontend deve apontar à API correta e esta à origem exata. Não colocar segredos em NEXT_PUBLIC_*. Para Cloudflare, usar npm run build:cloudflare seguido de preview e deploy apenas com autorização do responsável. O repositório permite clonar sem acesso de administração; para escrever, Gonçalo usa fork/PR ou o proprietário concede acesso GitHub conscientemente. Não partilhar contas ou tokens pessoais.

Rollback: repor revisão PostgreSQL compatível e versão frontend anterior, verificando CORS/domínio. Render Free limita aos dois deploys anteriores. Não usar deploys inicialmente falhados como recuperação, não fazer downgrade destrutivo nem voltar a SQLite online. Backup/restauro Neon remoto ainda não foi ensaiado. Ler o relatório antes de alterações nos dados.

O que enviar: este guia, links do ramo e PR, pacote de alterações e ambos os relatórios. **Nunca enviar .env, .env.production, bases/dumps, strings Neon, Auth-Keys, passwords, cookies, tokens ou pastas de autenticação.** Acesso à app, colaboração no código e administração do alojamento são permissões diferentes. Não foi enviado convite/mensagem ao Gonçalo pelo assistente.
