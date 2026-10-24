# VALIDAÇÃO DE PUBLICAÇÃO — 24/10/2026

**Estado: candidato local; publicação deste lote pendente de confirmação.** Código de integração: `4e4a6098da492e7b926ac1e58c2e932815c58fd3`. Consultar o manifesto da entrega para a revisão final de documentação.

## Serviços existentes

- Interface: https://websecai-frontend.websecai-estg.workers.dev/ — Worker `websecai-frontend`, conta `bb7555a8db7a7682c3e860331bc214e7`.
- API: https://websecaiapi.onrender.com — Render `websecaiapi`, `srv-dbd4rj2fngtc73fk0d4g`, Free.
- Base: Neon WebSecCheckAI / websecai-validacao / neondb, projeto `morning-smoke-38536704`, branch `br-withered-bonus-b5nrod3w`.
- Repositório: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI ; novo ramo local `codex/integracoes-revisao-20261024`, ainda não enviado.

Último runtime identificado no trabalho anterior: código GitHub `1ee44cfeb4f77d8aee2ab1659173d671354956a2`, Render deploy `dep-dbdqk229lscs73aef270`, Worker versão `3dd06322-455f-4094-903a-016d31469db7`. Hoje confirmou-se o HEAD GitHub `28ac611f50a690c093f8db0f22d100f51764821c` (documentação posterior). Não se voltou a inspecionar o painel de deployments para atribuir um novo runtime a esses IDs; não houve publicação pelo assistente neste lote.

Verificação pública em 24/10/2026 10:49:27 UTC: página de recuperação HTTP 200, health ok, registo público fechado, rotas anteriores de alteração/recuperação presentes, CORS da origem correta aceite e proteção no-referrer/no-store. É uma verificação pública de continuidade, não autenticação de três pessoas nem validação de TI.

## Ordem proposta após aprovação

1. Comparar o ramo remoto de novo. Se tiver avançado, integrar as alterações novas e voltar a testar antes de substituir qualquer ref. Manter o ponto anterior para rollback.
2. Enviar apenas o ramo/revisão aprovados; o auto-deploy Render mantém-se desligado. Não alterar o repositório do grupo por substituição de pasta.
3. Confirmar ausência de investigações em curso com os três elementos. A pessoa introduz chaves privadamente e confirma apenas que guardou. Aplicar os limites e a janela inicial descritos em INTEGRACOES_E_LIMITES.md no backend correto.
4. Publicar primeiro backend na revisão aprovada. O arranque aplica a migração **20261024_03**, aditiva: tabela evidence_reviews, sem apagar ou alterar contas/evidências existentes. Migração vazia e idempotência foram testadas em PostgreSQL local, não no Neon real.
5. Validar health, OpenAPI/novas rotas e CORS. Só depois publicar o bundle compatível no Worker existente, sem criar serviços, planos ou domínios.
6. Cada pessoa inicia sessão na sua conta. Validar visualmente que vê as suas investigações e não as dos outros. Os testes deste lote usaram três utilizadores fictícios; falta a aceitação real dos três. O terceiro email/conta ainda precisa de ser identificado/configurado pela pessoa, se não existir.
7. Executar uma aceitação TI pequena e medida; verificar estados/horas/conteúdo seguro e CPU real do Worker nos painéis. Não confundir tempo de arranque de bundle com CPU por pedido.

## Planos e limites atuais

[Render Free](https://render.com/docs/free): adormece após 15 minutos, pode demorar cerca de um minuto a acordar, disco temporário e 750 horas por workspace/mês. Largura de banda e builds também têm limites. Sem método de pagamento, excesso pode suspender serviços/builds; com faturação ativa pode haver custos adicionais, pelo que se deve manter a condição sem cartão/extras aprovada. Não criar keep-alive. Não usar Render Postgres temporário em vez do Neon.

[Neon Free](https://neon.com/pricing): página consultada indica 100 CU-h/projeto/mês, 1 GB/projeto, até 2 CU e sem cartão. São valores documentais atuais, não leitura do consumo/contrato desta conta. PostgreSQL continua a guardar contas, investigações, quotas e revisões. Não ativar Better Auth, Object Storage ou outros serviços que a página passe a oferecer.

[Cloudflare Workers Free](https://developers.cloudflare.com/workers/platform/limits/): 100000 pedidos/dia e 10 ms CPU/pedido para código Worker; assets estáticos têm regras próprias. Compilar e correr localmente não comprova cumprimento de CPU em produção. A validação dos novos endpoints/dynamic routes e a amostragem de CPU real continuam pendentes do deploy autorizado.

## Rollback seguro

Não fazer downgrade destrutivo nem apagar a tabela de revisões. **A imagem antiga, sem migração 03, pode falhar no arranque por não reconhecer a revisão Alembic.** O patch rollback-seguro.patch repõe a aplicação anterior mas conserva `app/models/investigation.py` e a migração 03 para compatibilidade e preservação do histórico. O arranque e a retenção de dados fictícios foram testados localmente em SQLite.

Se for necessário: suspender aceitação TI, aplicar esse patch num ramo de correção, rever/testar, publicar primeiro o backend compatível e depois reverter o frontend para a versão anterior identificada. Preservar configuração, JWT e ligações Neon. Não usar simplesmente a imagem Render anterior depois da migração sem avaliar esta compatibilidade. O rollback exige a mesma confirmação humana de serviço/revisão; não foi aplicado online. Não reiniciar orçamentos para repetir testes.

A pessoa confirmou hoje que a password Neon exposta foi substituída e as duas ligações Render atualizadas; é confirmação humana, sem inspeção dos valores pelo assistente.
