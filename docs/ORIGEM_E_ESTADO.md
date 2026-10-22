# Origem e estado da integração

- Destino autorizado: `tiago990-rbot/ESTG-ESII-WebSecAI`.
- Commit remoto anterior: `1b74f9ca5c5b296e935122e21e9000c4be26c378`; continha apenas `README.md`.
- Base: ZIP `WebSecAI_Continuacao_2026-10-22_v2.zip`, SHA-256 `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`.
- Manifesto original: 138 ficheiros verificados, zero diferenças antes de alterações.
- Revisão local testada: `38b3c378ee1ad002850e1a2bf5cb7843ab0b2252`, criada a partir do ZIP; não é um commit anterior deste remoto.
- Ramo de integração: `codex/publicacao-gratuita`, baseado no histórico do GitHub; sem force-push.
- Código e formulário Windows exportados de ficheiros versionados; configurações privadas, bases e sessões excluídas.

Validação anterior à integração: suite original com 98 testes; versão adaptada com 105 testes aprovados/um omitido em SQLite e 106 aprovados em PostgreSQL local real. Bundle Cloudflare e navegador no workerd local com API/PostgreSQL aprovados para três contas sintéticas. Histórico e sessão preservados após reinício local.

Destinos identificados: Neon `WebSecCheckAI` em AWS Ohio; conta Cloudflare com subdomínio `tmelo1715.workers.dev`; Render `Tiago's workspace`. Ainda não há URLs públicos WebSecAI confirmados. O painel Cloudflare mostrou 0/100 000 pedidos hoje. A etapa inicial não tinha recursos remotos. Depois foi criada a branch Neon Free `websecai-validacao` (`br-withered-bonus-b5nrod3w`), com esquema apenas e sem expiração; o ramo original foi preservado. O formulário Render Free está preparado, sem serviço criado.

Faltam a configuração humana de segredos, os testes na branch de validação Neon já criada, o deploy e a aceitação dos três elementos em máquinas distintas. URLhaus continua sem chave nesta instalação e sem consultas reais. Zero chamadas reais Tavily/Groq foram efetuadas pelo assistente.

Os relatórios desta preparação encontram-se em `VALIDACAO_URLHAUS.md` e `VALIDACAO_PUBLICACAO.md`. As referências a ausência de push descrevem a etapa anterior ao envio desta integração; registar os commits e IDs de deploy efetivos quando realizados.

Integração enviada: `e926bd4a323b68978475a83bf8cc797cd1c5c690`, árvore `ed39e523a1bca8acdf07c2e07900e944b4df181b`; comparação remota exata. Revisão: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19 . O commit posterior de documentação regista este checkpoint; não altera o código testado.
