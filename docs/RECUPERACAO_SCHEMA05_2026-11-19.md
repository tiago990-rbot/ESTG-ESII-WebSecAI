# WebSecAI — recuperação compatível com a migração 05

Este ramo é uma alternativa de recuperação do backend, preparada a partir do lote A (`248d72e`). Mantém os limites, reservas, auditoria e proteções de aceitação. Conhece a migração `20261030_05` e os modelos das três tabelas do Lab, mas não disponibiliza os percursos do Security Lab. A documentação principal do grupo foi preservada a partir de `b37ca65`.

## Evidência local de 19/11/2026

Numa instância PostgreSQL descartável em `127.0.0.1`, a versão integrada criou a cabeça 05. Inseriram-se uma conta fictícia, um projeto fictício e os contadores históricos de aceitação 1 URLhaus / 2 Tavily / 2 Groq. As operações de arranque desta alternativa (validação local, Alembic e recuperação de tarefas interrompidas) passaram. As linhas e a cabeça 05 ficaram exatamente iguais; o contrato `/api/v1/usage` existe e os percursos `/api/v1/lab` estão ausentes. O servidor de testes foi parado. Não houve chamadas reais aos fornecedores.

O primeiro ensaio local em SQLite terminou por tempo excedido. O ensaio PostgreSQL ficou aprovado depois de corrigir a inspeção do contrato no próprio teste. Este ensaio não é uma restauração de produção nem prova das contas reais.

## Procedimento se for necessário recuperar

1. Suspender novos pedidos e confirmar ausência de tarefas em curso.
2. Preservar a base, as credenciais privadas, os contadores e `TI_ACCEPTANCE_ID`. Não executar downgrade nem alterar a tabela Alembic.
3. Usar primeiro a versão integrada com `SECURITY_LAB_ENABLED=false` e `PROVIDER_USAGE_SYNC_ENABLED=false` se isso resolver o problema.
4. Se for necessário este backend alternativo, publicar este ramo no mesmo serviço Render Free, com as ligações e restantes variáveis existentes. Usar uma interface anterior compatível com o contrato A, pois esta alternativa não serve o Lab.
5. Verificar saúde, autenticação, isolamento e histórico sem consumir fornecedores. Uma recuperação da base exige decisão separada e avaliação das escritas posteriores ao ponto guardado.

Nunca selecionar os deploys antigos `e55b8f9` para recuar depois da migração 05: desconhecem as revisões 04/05.
