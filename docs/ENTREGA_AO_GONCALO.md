# Entrega e continuação WebSecAI — v5 integrada, 23/10/2026

Interface: https://websecai-frontend.websecai-estg.workers.dev — API: https://websecaiapi.onrender.com.

As melhorias v5 do Gonçalo estão integradas: identidade, arquivo/formulário, filtros, cronologia, mapa de proveniência e correções de acesso/sessão. O registo público continua fechado e a interface agora explica o acesso ao grupo.

Código GitHub: af196b2780916e3aa2029cc1d1c1e0352471df0d. Usar o ramo **codex/publicacao-gratuita**, não main: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/tree/codex/publicacao-gratuita. Revisão no PR #19: https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19. Render Live dep-dbdjdmon74is7390qdog; Cloudflare cf9dd8ba-9473-4980-871f-395be87334e0. Relatórios posteriores não mudam a revisão executada.

114 testes PostgreSQL e testes JS passaram. No navegador local workerd+FastAPI+PostgreSQL: três contas sintéticas, demo/PDF/isolamento, cronologia/mapa/teclado, móvel e reinício passaram. Houve publicação remota real e testes públicos HTTP/política/CORS. Não houve login real do grupo nem consultas reais a fornecedores. Ver VALIDACAO_PUBLICACAO.md.

Pendências: a pessoa ainda não confirmou rotação da credencial Neon exposta; seguir CRIAR_CONTAS_PASSO_A_PASSO.md e criar contas privadamente. Falta aceitar demo/PDF/isolamento online e identificar o terceiro email. O frontend continua com consumo CPU acima do teto Free na pequena amostra inicial: 6 invocações, mediana247,35ms,0erros; não é aceitação de estabilidade. Preparar uma solução estática/cliente no mesmo Cloudflare, com testes e sem plano pago, se for a próxima tarefa autorizada. Backup/restauro remoto também está pendente.

Para uma instalação nova, clonar o ramo acima. Para uma cópia do grupo já alterada, preservar dados e configuração privada, criar um ramo de integração e comparar manifesto/patch. O pacote WebSecAI_devolucao_alteracoes.zip contém apenas alterações cumulativas sobre o ZIP original v2; não é uma pasta completa. Ver INTEGRACAO_DO_PATCH.md. A base foi o ZIP v2, não o GitHub. O patch recebido v5 era cumulativo v4/v5 e foi integrado por ficheiros/hashes, sem forçar conflitos. A devolução atual contém um novo patch cumulativo validado sobre a base original.

Instalação local ensaiada: Python3.12.14, Node24.19.0; backend criar venv e instalar requirements-dev.lock.txt, executar scripts/setup_local.py e uvicorn app.main:app em loopback8000. Frontend npm ci e npm run dev em3000. As demonstrações fictícias não exigem chaves Tavily/Groq. Testes destrutivos PostgreSQL só em loopback/base websecai_test_*. Nunca no Neon.

URLhaus: zero consultas reais nesta passagem; máximo2 após configuração humana privada. Não apagar o contador de tentativas, visitar alvos maliciosos ou chamar Tavily/Groq para validar URLhaus. Configuração, autenticação e no_results são estados distintos. Tavily/Groq só com pequeno orçamento humano confirmado, sem repetir lotes antigos; limites online preparados a zero. Não configurar credenciais por chat ou NEXT_PUBLIC_*.

App, colaboração GitHub e administração dos fornecedores são permissões distintas. Gonçalo só precisa de conta WebSecAI para usar a app; não de ligações Neon ou contas pessoais de Tiago. As investigações continuam privadas por dono. Não foram enviados convites/mensagens nem concedidas permissões GitHub pelo assistente.

Deploys manuais, um processo/instância, aguardar tarefas antes de publicar/reverter. Usar Free sem cartões, domínios pagos, keep-alive ou automações. Render adormece após15min e Neon também suspende compute. Não é necessário manter o portátil ligado para servir a app. Ler rollback/CPU/quotas no relatório antes de continuar.

Não enviar .env, .env.production, bases/dumps, passwords, Auth-Keys, strings Neon, tokens, cookies, logs, capturas de credenciais ou pastas de autenticação. Os launchers locais não são um instalador portátil. O pacote e relatórios são a entrega segura para integração.
