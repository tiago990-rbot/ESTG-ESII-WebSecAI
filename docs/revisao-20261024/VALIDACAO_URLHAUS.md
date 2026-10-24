# VALIDAÇÃO URLHAUS — lote de 24/10/2026

**Consultas reais neste lote: zero.** Não foram visitados URLs maliciosos nem feitas verificações técnicas de terceiros. Consultar o relatório anterior para o histórico; não reutilizar os seus lotes como autorização para repetir consultas.

O adaptador oficial existente foi preservado. Um HTTP 200 com query_status no_results é distinto de chave ausente, HTTP 401/403 e HTTP 404. Um 404 passou a erro de consulta: não comprova autenticação nem ausência de correspondências. Testes controlados cobrem esta distinção; não é autenticação real no fornecedor.

A chave local não é prova de chave no Render. A pessoa configura URLHAUS_AUTH_KEY no Environment do backend, nunca no frontend, Git ou chat. Não se leu .env, clipboard ou campos de credenciais.

Após aprovação do candidato e introdução privada da chave: ativar a janela inicial TI_ACCEPTANCE_ENABLED=true / TI_ACCEPTANCE_ID=20261024, que bloqueia mais de duas reservas URLhaus na base, inclusive após reinício. Fazer uma única consulta por domínio através da investigação pública, com modo técnico desligado e opcionais desmarcadas. Registar hora UTC, estado seguro, número de referências e se houve autenticação válida. Repetir só se ainda houver margem nas duas consultas e motivo concreto; não alterar ID/contadores para contornar o teto. As duas pesquisas Tavily da mesma investigação já esgotam a sua janela inicial de dois pedidos.

A consulta pode não devolver resultados. Isso valida apenas a consulta/cobertura indicada, nunca a segurança do alvo. Se o fornecedor rejeitar a chave ou responder 429, parar e reportar o estado. A síntese IA é atualizada por último, reutilizando o que já foi recolhido.

[Documentação oficial URLhaus](https://urlhaus.abuse.ch/api/) consultada em 24/10/2026: Auth-Key e condições comunitárias gratuitas. Limites efetivos/acesso do titular continuam por aceitar no servidor.
