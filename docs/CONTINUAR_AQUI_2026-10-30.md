# Continuação e integração — WebSecAI, 30/10/2026

Esta é uma entrega de desenvolvimento **local**, para o colega que gere Render, Neon e Cloudflare. Não prova que estas alterações estejam publicadas. O utilizador autorizou trabalho local, sem gastos, publicação, novas chamadas reais a fornecedores ou testes intrusivos. A futura operação remota exige o responsável e o âmbito específico dessa operação.

## Começar pelo código correto

Base: `e55b8f919ac25dfc59e253bb47be03d83b91efb7`, ramo `codex/integracoes-revisao-20261024`, clonado separadamente em 30/10. O `main` observado não era a base do código completo. Não reaplicar o ZIP v7 antigo nem substituir o repositório do grupo por uma pasta inteira.

Há dois incrementos: A, quotas/diagnóstico, termina em `b49d314930ef43b8a0bfcb83b74a5e6b8c6db70c`; B acrescenta o Security Lab e esta documentação. O manifesto exterior do pacote identifica a revisão final e os hashes. Os commits são locais, sem push. O lote A tem uma revisão independente com a correção UTC, no ramo local codex/quotas-only-20261030; aplicar os patches sequenciais, sem assumir que os dois snapshots formam uma cadeia simples de cherry-picks.

Antes de aplicar: identificar o ramo e o SHA efetivamente publicados, verificar alterações posteriores à base e preservar as alterações do colega. Num checkout de integração limpo, verificar `git apply --check` para o patch A; aplicar/rever A e depois verificar/aplicar B. Se a base mudou, fazer merge das alterações relevantes, resolvendo diferenças; não forçar `--reject`, apagar ficheiros ou repor o snapshot antigo. O snapshot incluído serve para comparação e recuperação de código, não substitui dados ou configuração.

## O que muda no lote A

Página `/usage` com configuração, reservas partilhadas, limites internos, restante, datas UTC convertidas para Lisboa, bloqueios conhecidos, aceitação inicial e informação externa com origem/data. GET do painel não chama fornecedores. Render, Neon e Cloudflare aparecem com valores desconhecidos e ligações às consolas; não há acesso às contas de infraestrutura nem contadores inventados.

As reservas usam atualização condicional na base de dados. Não há reposição ou apagamento de contadores. Uma reserva pode ficar contabilizada mesmo se uma proteção posterior ou a rede impedir a chamada: são reservas conservadoras, não faturação.

Groq: só se guardam campos numéricos documentados dos headers, por modelo. Pedidos/dia e tokens/minuto são dimensões diferentes; outros limites podem existir. `Retry-After` conhecido e saldo observado insuficiente impedem novas chamadas. Metadados não substituem o painel da conta; outras aplicações podem consumir a mesma quota. Uma observação não é uma garantia de saldo em tempo real.

Tavily: consulta administrativa opcional a `GET /usage`, por botão separado, com opt-in no servidor, uma tentativa por janela UTC de cinco minutos e dez por dia. Lê apenas limites/utilização numéricos da conta e da chave. Não faz pesquisas, não altera plano nem crédito, não inventa renovação que não conste da resposta. Foi testada com respostas simuladas; não foi chamada nesta entrega. O contador da pesquisa continua separado. Uma pesquisa pública normal pode fazer duas chamadas basic, cada uma com a sua reserva.

“Autorizar +1 neste período”: só IDs de utilizadores explicitamente definidos em `QUOTA_ADMIN_USER_IDS` podem usar o endpoint. Motivo obrigatório, identificador idempotente, auditoria e máximo de três exceções por período. Não admite exceção com módulo desativado. Não altera plano, teto de segurança, limite por minuto, janela inicial de aceitação, janela privada de trabalho ou bloqueios do fornecedor. Um +1 é uma reserva adicional; pode ser usado por outra operação do grupo que chegue primeiro.

A recuperação de formato IA não faz uma segunda chamada automática bloqueada no mesmo minuto. `GROQ_RESPONSE_FORMAT=json_object` é uma opção explícita do responsável se o formato schema for incompatível; ambas as vias validam a resposta antes de a guardar. Cada nova tentativa manual usa quota.

## Variáveis novas / revistas — inserir privadamente no backend

| Variável | Valor inicial recomendado / significado |
| --- | --- |
| `QUOTA_ADMIN_USER_IDS` | Vazia até o grupo identificar os IDs autorizados; não inferir pelo nome/email |
| `PROVIDER_USAGE_SYNC_ENABLED` | `false`; ativar apenas após aceitar a consulta Tavily de metadados |
| `SEARCH_MONTHLY_LIMIT` | 200 reservas/mês UTC; teto de segurança 1000 |
| `AI_DAILY_LIMIT` | 10 reservas/dia UTC; teto 100; minuto continua limitado a 1 |
| `URLHAUS_DAILY_LIMIT` | 20 reservas/dia; teto 100 |
| `KEV_DAILY_LIMIT` | 5 atualizações/dia; cache de 24 horas preservada; teto 20 |
| `PHISHTANK_DAILY_LIMIT` | 0, desativado; chave também exige limite positivo |
| `HIBP_CATALOG_DAILY_LIMIT` | 0, opt-in público sem chave paga |
| `HIBP_VERIFIED_DAILY_LIMIT` | 0; API de contas de domínio verificado é distinta e condicionada a subscrição |
| `URLSCAN_DAILY_LIMIT` | 0, opt-in e chave; apenas pesquisa scans públicos anteriores |
| `PHISHTANK_ANONYMOUS_ENABLED` | `false`, opt-in distinto da chave |
| `GROQ_RESPONSE_FORMAT` | `json_schema`; alternativa `json_object`, sem repetição imediata |
| `SECURITY_LAB_ENABLED` | `false` até rever e aceitar o lote B |

Manter chaves só no backend. Não colocar API keys, ligação Neon, JWT, passwords ou cookies em `NEXT_PUBLIC_*`, código, ZIP, chat, capturas ou logs. Não substituir configurações existentes pelo `.env.example`. Os valores acima são limites nossos, não uma descrição do plano da conta.

## Lote B — Security Lab para código

Entradas: código em texto, vários ficheiros ou ZIP filtrado UTF-8. Até 40 ficheiros, 30 KB/ficheiro, 150 KB no total, ZIP comprimido até 1 MB. Caminhos relativos simples; sem `.env`, chaves privadas, dependências instaladas, binários, symlinks, ZIP cifrado ou caminhos fora da pasta. Uma pasta completa com README/ficheiros não suportados pode ser rejeitada: preparar um ZIP apenas com o código relevante. Não há clone remoto automático.

Os originais não são executados nem guardados integralmente: a aplicação persiste texto redigido e hashes da revisão original. A redação é heurística e não deteta todos os segredos. O utilizador deve rever e remover dados privados antes de enviar. Não testar credenciais encontradas.

Existem duas tarefas IA diferentes, ambas com consentimento explícito e orçamento Groq partilhado:

1. **Rever código**: recebe apenas uma seleção de código, independentemente dos resultados de scanners. No máximo 12 ficheiros e orçamento conservador de contexto. O histórico indica as linhas realmente incluídas. Hipóteses referenciam ficheiros/linhas visíveis; referências inexistentes são rejeitadas.
2. **Cruzar achados**: interpreta os resultados e prioriza acompanhamento. Uma correlação exige pelo menos duas ferramentas/origens distintas. A seleção é limitada e declarada; não afirma exploração. Alterar achados/revisões invalida a atualidade da síntese anterior.

Importação de JSON nativo/SARIF 2.1.0: Semgrep, OSV e Gitleaks. Só caminhos/linhas presentes na revisão; digest deve corresponder ao manifesto. Caminhos absolutos/URIs codificados não são aceites diretamente: usar o runner ou preparar caminhos relativos corretamente. Campos arbitrários são descartados; valores Secret/Match/Line/Author/etc. de Gitleaks não são apresentados. Importação não atesta a execução ou autenticidade do motor. OSV não fornece uma linha exata: mostrar apenas localização no ficheiro.

Histórico por dono, limites de 10 projetos e três envios/hora, 16 execuções/importações por revisão. Anotações humanas têm sequência/auditoria e rejeitam escrita concorrente desatualizada. Marcar “corrigido” não executa testes nem altera o código. Cancelar descarta o resultado; não devolve quota nem garante cancelar um pedido externo já enviado. Após reinício, uma análise em curso fica interrompida; não se repete automaticamente. Para reapreciar código corrigido, guardar uma nova revisão.

PDF: identidade WebSecAI, leitura executiva ou síntese IA quando existe, cobertura, barras por origem, cronologia dos registos, mapa de localização, prioridades/correlações, achados e inventário. Exportar não chama modelos nem motores. O PDF de exemplo incluído está rotulado como fictício e contém texto IA simulado; não o usar como prova de qualidade de um modelo real.

## Runner — executar fora do servidor público

Consultar `tools/security_lab/README.md`. O site funciona por importação; não executa scanners pesados no Render nem oferece comandos arbitrários aos visitantes. O runner CLI é uma ferramenta manual separada; não é um serviço remoto, uma fila persistente ou uma sandbox de sistema operativo.

Gitleaks 8.30.1 foi executado realmente em duas fixtures: um marcador intencional no caso vulnerável e nenhum no corrigido. Isso valida o fluxo do motor e a redação nesses casos; não mede cobertura geral. Semgrep e OSV só têm adaptadores/contratos testados nesta máquina. Preparar um ambiente Linux/CI descartável do grupo e validar motores, versões, regras/licenças e recursos antes de os anunciar como operacionais. Sem instalação automática de Docker/virtualização ou serviço pago.

## Migrações, publicação e recuperação — com o responsável

Migrações aditivas: `20261030_04` cria auditoria de exceções e observações; `20261030_05` cria projetos/execuções/revisões do Lab. Preservam contadores, contas, dossiês e revisões existentes. A aplicação chama upgrade no arranque; preparar a base e a recuperação antes de arrancar a nova versão no ambiente partilhado.

1. Identificar e preservar a revisão do serviço, configurações privadas, dados e um backup/recuperação verificado. Não copiar dados reais para este pacote.
2. Ensaiar as migrações e a subida da aplicação numa base de testes apropriada. A suite destrutiva **nunca** deve usar Neon de produção. `TEST_DATABASE_URL` só aceita localhost e nome `websecai_test_*`.
3. Validar a cópia de segurança e compatibilidade antes de aplicar no Neon. Usar ligação direta de migrações da mesma base, guardada privadamente; manter TLS e isolamento existentes.
4. Publicar backend compatível com as tabelas novas antes do frontend. Manter Lab desativado inicialmente. Preservar a lista dos três membros e o CORS exato.
5. Configurar administrador por ID. Rever quotas reais e planos gratuitos; manter PAYG/autoupgrades desligados. Não apagar a janela inicial de aceitação para “resolver” o bloqueio observado.
6. Rever/ativar o Lab estático e o consentimento de envio ao modelo. Não conectar um runner com acesso aos segredos do serviço ou à rede interna.
7. Compilar Cloudflare no ambiente do colega com o URL HTTPS certo da API. Os builds locais de teste podem usar localhost explicitamente; não publicar esses artefactos.
8. Aceitação humana: três contas isoladas, painel a refletir reservas, +1 só por admin, datas/429, caso TI com fontes reais, IA/PDF e revisão de código com referências. Definir previamente os pedidos/quotas exatos e confirmar planos gratuitos antes de novas chamadas reais. Não repetir os antigos 1 URLhaus/2 Tavily/2 Groq: essa autorização já foi consumida.

Não executar downgrade destrutivo: estas migrações recusam apagar o histórico. Para recuar, suspender novas tarefas e voltar ao código compatível, preservando as tabelas; rever os guards que a versão antiga não conhece. Restaurar dados apenas a partir de um procedimento ensaiado e decidido pelo responsável. Nenhuma restauração remota foi feita aqui.

## Validação e pendências

Consultar `VALIDACAO_LOCAL_2026-10-30.md` e o manifesto final do pacote. Testes/build locais não provam runtime no Render, ligações Neon, publicação Cloudflare, qualidade de IA real, ou quotas reais disponíveis. A verificação visual automática no browser foi interrompida pela ferramenta, que não conseguiu confirmar o URL; não foi contornada. O colega/grupo deve confirmar UI desktop/mobile e o percurso completo no ambiente de testes.

Próximo passo do colega: comparar a base, rever os dois incrementos e ensaiar migrações/configuração. Não começar por reenviar credenciais ou publicar cegamente o ZIP.

## Fase C — só desenho, não ativada

Pentest/DAST exige ambiente de staging do grupo, prova de controlo (por exemplo desafio DNS/ficheiro), autorização de quem tem autoridade, alvos/portas/caminhos definidos, isolamento do runner e limites de pedidos/duração/concorrência. Um checkbox de quem escreve um URL não chega. Redirecionamentos/subdomínios/serviços terceiros não herdam autorização.

Começar por laboratório fictício próprio. Depois poderá existir um perfil ZAP baseline e, separadamente, testes ativos planeados, com lista permitida, bloqueio de rede interna/metadata/terceiros, logs sem segredos, cancelamento e paragem global. Não há ativação pública ou testes ativos neste lote. A funcionalidade de verificar passwords próprias continua adiada.

## Referências técnicas consultadas em 30/10

- [Groq: rate limits e significado dos headers](https://console.groq.com/docs/rate-limits).
- [Tavily: GET usage](https://docs.tavily.com/documentation/api-reference/endpoint/usage) e [créditos](https://docs.tavily.com/documentation/api-credits).
- [Semgrep: schema JSON](https://github.com/semgrep/semgrep-interfaces/blob/main/semgrep_output_v1.jsonschema).
- [OSV-Scanner: formatos](https://google.github.io/osv-scanner/output/).
- [Gitleaks: CLI, redação e licença](https://github.com/gitleaks/gitleaks).

As condições do fornecedor e a conta real prevalecem sobre exemplos documentais. Não foram ativados pagamentos ou criados acessos externos.
