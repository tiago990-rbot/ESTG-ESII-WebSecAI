# Validacao: convites e passwords no site — 23/10/2026

## Resultado

Fonte 3d3d70da8712c899b920a6b062e63a2c2bb7bd37; codigo remoto 1ee44cfeb4f77d8aee2ab1659173d671354956a2, ramo codex/publicacao-gratuita e PR19. Render dep-dbdqk229lscs73aef270, Live confirmado no painel. Cloudflare 3dd06322-455f-4094-903a-016d31469db7, apenas ASSETS, startup31ms (nao e CPU por pedido). https://websecai-frontend.websecai-estg.workers.dev — API https://websecaiapi.onrender.com . A revisao anterior ativa no Render era 4fc733b4a314de2ee97f50216289329a8fdafcd9, observada no painel.

Funcionalidades novas: Alterar palavra-passe no Perfil mediante confirmacao da atual; convite de conta pendente com definicao privada da password no site; reposicao por link de uso unico emitido pelo responsavel depois de verificar a identidade. Sem password padrao, envio automatico de emails ou novos fornecedores. Login normal depois da definicao, sem auto-login. Registo publico fechado e allowlist preservada.

## Seguranca e migracao

Nova migracao aditiva 20261023_02: users.auth_version, users.password_ready e tabela account_actions. Preserva utilizadores/hashes/IDs/dossies existentes. Contas anteriores comecam ativas/versao0; tokens antigos sem versao so continuam validos enquanto a conta estiver na versao0. Alterar/repor a password incrementa a versao e rejeita tokens anteriores em todas as rotas protegidas. Termina as sessoes apenas dessa conta, sem alterar o JWT_SECRET global. Sem novas dependencias.

Tokens aleatorios256bits, so SHA256 guardado na base; finalidade/conta/versao/validade vinculadas. Convite24h, reposicao30min; token substituido ou usado torna-se invalido. Emissao de reposicao nao altera a password nem termina sessoes antes da utilizacao. Conta pendente nao pode entrar antes de definir password. Verificacao da allowlist tambem ao utilizar o link. Confirmacao de password,16–128caracteres; PBKDF2existente600000iteracoes preservado. Atualizacao condicional e consumo transacional rejeitam concorrencia/replay. Rate limit existente aplicado as duas rotas novas.

Token apenas no fragmento #token do link e no corpo HTTPS da API; removido da entrada atual do historico quando lido, sem persistencia localStorage e com no-referrer/noindex. Abrir novo fragmento no mesmo separador e tratado. Um link continua a ser uma credencial: a pessoa envia-o diretamente ao destinatario pelo canal privado e nao ao assistente/Git. O emissor scripts/issue_account_link.py exige consola interativa e ligacao Neon oculta introduzida pela pessoa, recusa pooling, verifica TLS/host oficial e nao le ficheiros .env. Nao existe endpoint publico de emissao de links nem alteracao da allowlist atraves destes formularios.

## Verificacao efetiva

- PostgreSQL18 local:152testes aprovados,105,05s; migracao vazia/repetida e migracao desde schema v7 com conta preservada, concorrencia de consumo e isolamento. Um aviso herdado TestClient/httpx.
- SQLite local:151aprovados,1teste especifico PG omitido,112,68s; dois avisos. A primeira execucao teve11erros de pasta temporaria do ambiente; repetida com basetemp dentro do workspace e aprovada.
- Onze testes novos de acesso: convite, ativacao, password atual errada, confirmacao, nova password, expiracao, substituicao, uso unico, membro removido, tokens antigos/JWT revogados, migracao e concorrencia. Um primeiro teste tinha uma rota demo incorreta; corrigida para a rota existente.
- Build Next/OpenNext e regressao JS auth/evidencias aprovados. Skill React aplicada: labels, autocomplete, erros acessiveis, estado de envio e limpeza dos listeners/segredos apos sucesso.
- Navegador390px -> workerd local -> API offline -> PostgreSQL: convite/definicao privada, login normal, Perfil/alteracao, reposicao, replay rejeitado, sessao antiga401, fragmento removido e novo link no mesmo separador;0erros JS,0pedidos externos. O primeiro ensaio detetou a falta de resposta a hashchange no mesmo separador; implementada e reensaio aprovado.
- Regressao de3contas sinteticas, demo7referencias, PDF, cronologia/mapa/teclado, rotas dinamicas e reinicio API+PG aprovada. Dados/credenciais exclusivamente ficticios nestes ensaios.
- Remoto:pagina/reset-password200; API/healthok; configuracao/registo fechado; OpenAPI com as duas rotas novas; CORSPOSTreposicao correto. Data 2026-10-23T18:41:45.526543+00:00.50ficheiros frontend do bundle iguais ao commit, normalizando CRLF.

Zero chamadas reais URLhaus/Tavily/Groq, zero links reais emitidos e zero passwords reais alteradas pelo assistente. A pessoa ja relatou login real anterior; a aceitacao dos formularios novos com contas reais cabe a pessoa em privado. Nao foram lidas credenciais, .env, clipboard ou base real. A migracao de producao foi executada pelo arranque hospedado; nao foi extraida a base para inspecao. Nenhum plano pago, cartao, dominio, automacao ou servico adicional.

## Operacao e limites

Seguir CONTAS_E_PASSWORDS_NO_SITE.md. Gerir_Convites_WebSecAI.cmd e local desta maquina. Para o Goncalo:opcao1secontanova/pendente, opcao3secontajaativa; receberlink e escolher a propria password. Tiago pode usar Perfil ou opcao2seesqueceu a atual. Ter nome/email na allowlist nao cria conta. Ter acesso ao site nao da acesso aos dossies dos outros nem a administracao Neon/Render/Cloudflare. Terceiroemailcontinua por identificar.

Nao ha emails automaticos de notificacao; confirmar a conclusao pelo canal habitual sem passwords. O utilitario antigo de alteracao direta foi substituido e o launcher antigo apenas apresenta instrucoes. O responsavel com acesso administrativo a base mantem capacidade de gerir contas; os links evitam conhecer a password pessoal escolhida.

RenderFreepodeadormecer15min e levar cerca1min no primeiro acesso. A primeira tentativa dep-dbdq1k3l550s73809png falhou em18m23s por timeout da detecao de porta, apesar de registar Uvicorn em0.0.0.0:10000; os testes publicos tiveram timeout60s. Uma consulta ao painel ficou retida31min na revisao automatica de permissoes e expirou, sem alteracoes nesse intervalo. A repeticao do mesmo commit, sem alteracoes de codigo/configuracao, ficou Live em39s, em23/10/2026as18:40:48UTC. A causa exata da falha inicial nao foi determinada; nao se apresenta a repeticao bem-sucedida como correcao de codigo. Sem garantia de disponibilidade. O risco de CPUCloudflareFree documentado na validacao v7 continua pendente; nao se fez teste de carga nem se ativou Paid. Backup/restauro remoto continua por ensaiar. A rotacao anterior da credencial Neon exposta nao foi confirmada pelo assistente e mantem-se obrigatoria se ainda pendente.

## Revisao e rollback

Rever https://github.com/tiago990-rbot/ESTG-ESII-WebSecAI/pull/19 . O patch/ZIP sao cumulativos sobre o manifesto original v2; so codigo/documentacao/evidencias sinteticas, sem chaves, base, logs, sessoes ou dependencias. Main preservado. Documentacao antiga incluida e historica; prevalece esta adenda sobre as afirmacoes de que v7 nao tinha novas tabelas ou mudanca de password.

Evitar voltar ao backend anterior a auth_version depois de usar este fluxo: o codigo antigo nao verifica a revogacao dos tokens, podendo aceitar sessoes anteriormente revogadas. Preferir correcao para a frente ou rollback de interface mantendo backend com verificacao de versao. Se for indispensavel backend antigo, a pessoa tem de planear a invalidacao global das sessoes/links no painel privado antes da reabertura; nao remover colunas/tabelas nem restaurar passwords expostas. Nao executar downgrade destrutivo. Aguardar tarefas em curso antes de novo deploy; dados persistem no Neon. Quotas/planos/CORS atuais preservados. Rollback de dados exige copia verificada em base separada, ainda nao ensaiado.

Referencia: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html . Sem garantia de qualidade de IA/fornecedores a partir destes testes de autenticacao.
