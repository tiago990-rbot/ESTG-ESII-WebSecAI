# Integrações, planos gratuitos e preparação privada

A pessoa confirmou os planos Free Tavily/Groq e os limites globais de **200 pedidos Tavily/mês UTC e 10 chamadas Groq/dia UTC** em 24/10/2026. Os valores de ficheiro e os valores por omissão foram preparados localmente. **Os valores reais do painel Render ainda não foram inspecionados/aplicados neste lote.**

## Backend correto, após confirmação da publicação

Render: `websecaiapi`, serviço `srv-dbd4rj2fngtc73fk0d4g`, pasta `codigo/backend`, Docker Free, um processo. Em Environment, a pessoa introduz privadamente `TAVILY_API_KEY`, `GROQ_API_KEY`, `URLHAUS_AUTH_KEY`. Não enviar chaves ou capturas ao assistente. Preservar DATABASE_URL, DATABASE_MIGRATION_URL, JWT_SECRET, CORS e lista de emails autorizados.

Configuração não secreta proposta para a primeira aceitação:

| Variável | Valor |
| --- | --- |
| SEARCH_MONTHLY_LIMIT | 200 |
| AI_DAILY_LIMIT | 10 |
| GROQ_MODEL | qwen/qwen3.8-27b |
| TI_ACCEPTANCE_ENABLED | true |
| TI_ACCEPTANCE_ID | 20261024 |

O modelo consta da documentação Free/structured outputs consultada; a disponibilidade efetiva nesta conta e a qualidade das respostas continuam por aceitar. O código limita a resposta a 3000 tokens, reduz o conjunto de evidências usando uma estimativa conservadora do tamanho e admite um pedido por minuto UTC partilhado. A estimativa não é um tokenizer exato nem garante ausência de HTTP 429. Os limites do fornecedor prevalecem. Não mudar para um modelo pago.

Cada pesquisa Tavily basic consome uma reserva; há até duas por investigação. Perguntas e eventual recuperação de formato Groq também reservam orçamento. As reservas são conservadoras e podem contar tentativas bloqueadas antes do HTTP; não as confundir com consumo efetivamente faturado pelo fornecedor. A janela inicial impõe no máximo duas reservas por fornecedor, persistentes na base. Não mudar TI_ACCEPTANCE_ID, desativar a proteção nem limpar contadores para repetir a aceitação sem nova decisão humana.

Guardar variáveis sem reiniciar pode não as aplicar. Fazer Save only enquanto se prepara o lote; aplicar no deploy autorizado, quando não houver investigações em curso. Não abrir o formulário de credenciais ao modelo nem copiar valores para ficheiros partilhados.

## Opcionais preparadas, ainda desativadas

- PhishTank: sem chave só com `PHISHTANK_ANONYMOUS_ENABLED=true` **e** PHISHTANK_DAILY_LIMIT positivo previamente acordado. Tem cache de uma hora, reserva diária/minuto, erros seguros e pausa após 429/509. A quota do fornecedor é variável; não se promete um número anónimo fixo.
- HIBP público: HIBP_CATALOG_DAILY_LIMIT=0 por omissão. Quando for aprovado um limite, usa GET `/api/v3/breaches?Domain=...`, sem chave de contas. Guarda nome/domínio, data explícita da fuga, datas do catálogo, classes de dados e incertezas. Não guarda emails, passwords ou HTML da descrição. Não confundir com o adaptador legado `/breachedDomain`, condicionado a subscrição e domínio verificado; não o ativar num trabalho de custo zero.
- urlscan: URLSCAN_DAILY_LIMIT=0 por omissão e sem chave nova. Uma eventual chave vai apenas para URLSCAN_API_KEY no Render. Apenas GET de scans públicos existentes, filtrados pelo domínio; nunca POST de novos scans. A infraestrutura de um scan não é atribuída automaticamente à organização.
- Cache minimizada no disco temporário do Render: perde-se após reinício/redeploy; reservas e pausas ficam no PostgreSQL. A data original da consulta é preservada e apresentada; a data de leitura da cache não é apresentada como nova consulta externa.
- Intelligence X: sem adaptador/licença, continua futuro.

## Documentação oficial verificada em 24/10/2026

[Tavily — créditos](https://docs.tavily.com/documentation/api-credits): oferta gratuita de 1000 créditos/mês; a instalação limita-se a 200 pedidos basic. [Groq — rate limits](https://console.groq.com/docs/rate-limits) e [structured outputs](https://console.groq.com/docs/structured-outputs): verificar no painel os limites reais da organização/modelo, incluindo tokens/minuto.

[URLhaus](https://urlhaus.abuse.ch/api/) requer Auth-Key e respeito pelas condições comunitárias. [PhishTank](https://phishtank.org/api_info.php) documenta app_key opcional, limites mais baixos e User-Agent identificável. [HIBP API v3](https://haveibeenpwned.com/API/v3) distingue catálogo público e contas de domínios. [urlscan — pesquisa](https://docs.urlscan.io/apis/urlscan-openapi/search) e [quotas](https://docs.urlscan.io/pages/api-rate-limits) documentam pesquisa histórica, chave e quotas por conta.
