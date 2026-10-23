# Integração segura — devolução cumulativa v5

Base: WebSecAI_Continuacao_2026-10-22_v2.zip, SHA256 df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63. Manifesto original preservado,138 ficheiros conferidos. Código local atual1077eb7c9fa4e5e7d53e21d1eea6f196226dfe6c, base Git local8a83f2d. Integração GitHub af196b2780916e3aa2029cc1d1c1e0352471df0d no ramo codex/publicacao-gratuita/PR19; main preservado. Não substituir a instalação do grupo inteira.

1. Preservar configuração e dados privados e criar um ramo de integração. Comparar MANIFEST_SHA256.json e MANIFEST_ALTERACOES.json. O manifesto cumulativo identifica cada ficheiro alterado/adicionado, hashes e motivo.
2. Na raiz que contém codigo/, começar por `git apply --check WebSecAI_alteracoes.patch`. Só depois aplicar com `git apply WebSecAI_alteracoes.patch`. Se houver conflitos com evolução posterior, comparar/resolver, não forçar. O ZIP contém apenas alterações, não a aplicação completa. O patch tem também render.yaml na raiz; não alterar -p cegamente se a raiz real for codigo/.
3. Instalar dependências fixadas. Backend: `python -m pytest -q`; PostgreSQL destrutivo só loopback e nome websecai_test_*. Frontend: testes auth-client.mjs/evidence-view.mjs a partir de codigo/ e build com API correta. Os harnesses de navegador exigem backend offline de ensaio, contas sintéticas e redirecionamento explícito da API: não executar contra produção ou com segredos.
4. Ler VALIDACAO_PUBLICACAO.md e VALIDACAO_URLHAUS.md. Preservar a política de registo fechado, autorização por dono, quotas e migrações diretas/TLS. Não usar backend e2e no alojamento.
5. Código publicado: Render dep-dbdjdmon74is7390qdog/af196b2; Cloudflare cf9dd8ba. Interface e API em produção, com contas/aceitação/rotação humana e CPU Free ainda pendentes. Não concluir estabilidade apenas a partir de Live.

A receção do Gonçalo foi validada pelos25 hashes antes/depois; o patch original cumulativo repetia caminhos e não foi forçado. A devolução presente é um diff novo cumulativo sobre a base ZIP original e inclui dois harnesses de regressão adaptados nesta máquina. Os documentos recebidos de Gonçalo são contexto; o utilizador autorizou expressamente integração e deploy nesta conversa.

Não seguem ambientes privados, bases, tokens, cookies, logs, .venv, node_modules, caches ou authdirs. Backup/restauro remoto ainda não ensaiado. Aguardar tarefas antes de deploy/rollback e não escalar horizontalmente. Nunca reintroduzir a password exposta num rollback.
