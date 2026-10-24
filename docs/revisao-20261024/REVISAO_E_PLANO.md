# WebSecAI — revisão local de 24/10/2026

Código preparado e testado localmente. **Este lote ainda não foi publicado.**

- Ramo local: `codex/integracoes-revisao-20261024`.
- Base local preservada: `3d3d70da8712c899b920a6b062e63a2c2bb7bd37`.
- Base GitHub confirmada por leitura do ramo: `28ac611f50a690c093f8db0f22d100f51764821c`.
- Revisão de código local: `6cbe92a27190f6489747a94e2bbc9f086dee49f7`.
- Revisão de código de integração, candidata: `4e4a6098da492e7b926ac1e58c2e932815c58fd3`.
- As revisões diferem porque têm históricos/documentação diferentes; os 27 ficheiros alterados de código/configuração são iguais nas duas cópias.

## O que mudou

Fontes essenciais (Tavily e URLhaus), síntese IA, contexto global KEV e opcionais estão separados. A nova investigação guarda explicitamente a seleção das opcionais, inicialmente vazia. Não selecionar uma opcional produz Não solicitado e não torna a investigação Parcial. Falhas em módulos pedidos mantêm Parcial. Investigações antigas sem esse campo conservam o âmbito original.

O contexto global KEV fica fora do mapa e da cronologia do alvo, da contagem de referências do caso e das diferenças entre recolhas. Mantém E#, anexo e vista própria. Candidatos por produto continuam identificados como candidatos sem versão confirmada. Os contadores distinguem dimensões e não representam incidentes.

O PDF equilibra páginas do mapa: 13 referências relacionadas com o caso passam a 7+6. Seleciona até 24 referências no mapa, conserva o resto no anexo e mantém datas independentes e UTC. As seis respostas IA vazias deixam de repetir o mesmo parágrafo. O exemplo entregue é inteiramente fictício: 13 referências do caso e 5 alertas globais.

A revisão humana acrescenta notas, estado, apreciação de identidade, autor, data e histórico apenas ao proprietário da investigação. Não permite editar/eliminar revisões anteriores. Rejeita uma gravação baseada numa revisão desatualizada. Alterar conteúdo da evidência assinala as revisões anteriores como antigas. Revisões tornam a síntese anterior desatualizada; não se chama IA automaticamente. Contestação ou identidade não correspondente não são enviadas como suporte positivo à IA. Uma marcação humana nunca passa a confirmação independente de intrusão.

PhishTank anónimo, catálogo público HIBP e pesquisa passiva urlscan foram preparados, mas ficam desativados e sem testes externos. Intelligence X permanece futuro. A funcionalidade de verificação de password própria continua adiada. Convites, ativação, alteração e recuperação de contas existentes foram preservados.

## Testes e limites da conclusão

- Base anterior: 152 testes PostgreSQL passaram.
- Suite completa deste lote: 173 testes PostgreSQL passaram; migração vazia e repetida passaram.
- Ficheiro final com os últimos casos HTTP 404: 23 testes adicionais/atualizados passaram em SQLite e em PostgreSQL local dedicado. Estes conjuntos sobrepõem-se; não somar como testes únicos.
- Compilação Next.js 15.5.28 / OpenNext 1.20.13 concluída para Cloudflare, com verificação de tipos. O aviso de suporte incompleto a Windows do OpenNext continua a existir.
- Navegador contra Worker local + FastAPI + PostgreSQL: três utilizadores fictícios, isolamento, demonstração, PDF, separação KEV, revisão humana, navegação por teclado, largura 390, reinício API/PostgreSQL e fluxos de convites/passwords. Zero erros JavaScript e zero pedidos externos no navegador.
- Exemplo PDF: 12 páginas renderizadas, revista a composição de todas numa folha de contacto e os dois mapas individualmente; 25 ligações internas válidas, sem glifos de substituição. Casos 0/12/13/25 exportados em testes.
- Rollback: aplicação anterior com modelo/tabela e migração 03 preservados inicia e mantém utilizador, investigação e revisão fictícios em SQLite. Não é prova de rollback no Neon real.
- Aviso de descontinuação Starlette/httpx nos testes; não impediu os resultados.

**Não houve chamadas reais Tavily/Groq/URLhaus neste lote: 0/0/0.** Fixtures e demonstrações não comprovam autenticação, quotas da conta ou qualidade semântica de um modelo. Não se acedeu a investigações/PDFs privados de produção.

## Próxima decisão humana

O pedido novo exige confirmação antes de alterações remotas. Ainda não houve push, criação de ramo remoto, mudança no Render, migração Neon ou deploy Cloudflare. Aprovar a revisão de entrega indicada no manifesto e os serviços existentes antes de prosseguir. Confirmar também que o grupo não tem investigações em curso. As chaves são introduzidas pela pessoa diretamente no Render.
