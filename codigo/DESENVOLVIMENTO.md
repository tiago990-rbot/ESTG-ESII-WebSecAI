# WebSecAI - guia de desenvolvimento local

21/10/2026. Evolução académica do WebSec Check recebido do ano anterior. Os originais e respetivo manifesto estão um nível acima de `codigo/`.

## O que existe nesta versão

| Área | Estado e limites |
| --- | --- |
| Contas, verificações DNS/TLS/HTTP, histórico e PDF herdados | Preservados, com correções de autenticação, rede e exportação |
| Investigações por domínio ou mensagem | Fluxo local funcional; progresso, evidências, fontes, histórico de observações e nova tentativa seletiva |
| URLhaus e PhishTank | Adaptadores implementados e testes controlados; aguardam chave e aceitação ao vivo |
| Notícias, fóruns e relatórios | Pesquisa Tavily implementada; duas consultas, deduplicação e alegações identificadas; aguarda chave |
| Exploração conhecida | Catálogo CISA KEV consultado ao vivo; cache de 24 horas. Alertas gerais separados de candidatos por produto |
| Síntese IA e perguntas | Groq implementado com JSON validado e referências obrigatórias; aguarda chave e avaliação com modelo real |
| Exposição | HIBP: apenas agregados de domínio verificado/configurado, sem guardar emails/passwords; acesso e licença por validar |
| Demonstração | Fictícia, identificada, sem rede nem LLM; permite conhecer o fluxo sem chaves |
| Comparação e PDF integrado | Implementados; excluem observações antigas dos resultados atuais e assinalam sínteses desatualizadas |
| IntelX, MCP e password própria | Por implementar; opcionais/condicionados conforme roadmap |

Um estado `not_configured`, `error` ou `no_results` tem um significado diferente. Nenhum deles certifica um website como seguro. O score mede observações técnicas e não a probabilidade de intrusão.

## Arranque numa nova máquina

Pré-requisitos: Python 3.12, Node.js 22 ou 24 e npm. Executar os comandos a partir de `codigo/`, em PowerShell. Não é necessário ativar o ambiente virtual.

Terminal 1:

```powershell
cd backend
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade 'pip==26.2'
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\Scripts\python.exe scripts/setup_local.py
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

O setup cria `.env` e um segredo aleatório se o ficheiro ainda não existir. Preserva configurações já existentes. As migrações Alembic são aplicadas no arranque, conservando as tabelas herdadas. Ao atualizar uma instalação com dados importantes, guardar previamente uma cópia da base com o servidor parado. O downgrade destrutivo não está disponível.

Terminal 2:

```powershell
cd frontend
npm.cmd ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm.cmd run dev
```

Abrir http://127.0.0.1:3000, criar uma conta e escolher **Experimentar demonstração** em Investigar. API e contratos: http://127.0.0.1:8000/docs. Para uma build otimizada, parar o frontend, executar `npm.cmd run build` e depois `npm.cmd start`.

Na máquina desta sessão não existe `py` de sistema. O ambiente `.venv` já está criado e pode ser usado diretamente. O bootstrap usado foi o Python incluído no runtime local do Codex; esse caminho não deve ser assumido noutra máquina.

## Configuração das fontes

Editar **privadamente** `backend/.env`. Nunca enviar este ficheiro para o GitHub ou incluí-lo num ZIP. Os nomes permitidos estão em `.env.example`.

No Windows, existe também `Configurar_APIs.cmd`: abre um formulário local com campos ocultos para Tavily/Groq e preserva as restantes definições. O passo a passo está em `../PROXIMO_PASSO_APIS.md`. Depois de guardar, reiniciar o backend. Para verificar apenas presença de configuração: `python scripts/verificar_ligacoes.py`, a partir de backend. O argumento `--live` verifica autenticação por metadados sem fazer pesquisa nem gerar texto; isto ainda não valida a qualidade da IA.

| Variável | Finalidade |
| --- | --- |
| JWT_SECRET | Assinatura de sessões; gerado pelo setup; mínimo de 32 caracteres |
| DATABASE_URL | SQLite local por defeito; executar o backend a partir da respetiva pasta |
| TAVILY_API_KEY | Pesquisa de notícias/fóruns/relatórios |
| GROQ_API_KEY / GROQ_MODEL | Modelo de síntese e perguntas; confirmar disponibilidade e suporte de JSON Schema na conta |
| URLHAUS_AUTH_KEY | Registos de distribuição de malware |
| PHISHTANK_API_KEY | Reputação do URL exato |
| HIBP_API_KEY / HIBP_VERIFIED_DOMAINS | Consulta de agregados apenas em domínios próprios efetivamente verificados na fonte |
| SEARCH_MONTHLY_LIMIT | Máximo local de pedidos de pesquisa por mês, predefinido 800 |
| AI_DAILY_LIMIT | Máximo local de pedidos ao modelo por dia, predefinido 40 |
| ALLOW_DEMO | Permite exemplos fictícios; `true` por defeito |
| CORS_ORIGINS | Origens locais autorizadas para o frontend |

Reiniciar o backend após alterações. Nenhuma chave foi configurada nesta entrega. Os limites locais são contadores de pedidos, não tetos monetários do fornecedor. Para manter 0 €, usar apenas planos sem faturação e confirmar a quota atual antes de ativar cada acesso. Não é preciso ativar HIBP/IntelX para demonstrar o núcleo de TI + OSINT + IA.

O catálogo público CISA não precisa de chave. Se a atualização falhar, a cache antiga mantém uma indicação da sua idade. Uma CVE adicionada ao KEV significa exploração conhecida dessa falha; não demonstra uma intrusão neste domínio. O campo Produto é uma pista declarada pelo utilizador, sem deteção/validação da versão instalada.

## Como os dados circulam e porquê

1. A API valida e normaliza o alvo. Queries/fragments são removidos para reduzir o envio de tokens e dados privados. Isto pode reduzir a precisão de uma consulta de URL.
2. A investigação recebe ID e estado persistidos. O navegador consulta o progresso, mantendo resultados mesmo se uma fonte falhar.
3. Os conectores fazem pedidos a endpoints fixos. A pesquisa externa recebe o domínio e, opcionalmente, o nome da organização. A pesquisa é limitada; não cobre todos os fóruns ou incidentes.
4. A mensagem original não é guardada na base. Aplicam-se padrões de minimização a emails, números e campos de credenciais; apenas sinais e links normalizados ficam guardados. Esta minimização não garante reconhecer todos os dados pessoais: não introduzir segredos reais.
5. A IA recebe até 20 evidências e a cobertura das fontes. A saída tem schema e IDs validados. Este controlo evita referências inexistentes; não prova que todas as interpretações do modelo sejam corretas. A avaliação humana continua necessária.
6. O relatório conserva fontes, datas conhecidas, incertezas e limitações. Publicação, incidente e consulta são campos diferentes; não inventamos datas de incidentes a partir das notícias.

As verificações técnicas fazem pedidos ao alvo e só devem ser ativadas num website próprio/autorizado. A proteção de rede rejeita destinos privados/reservados, valida todos os IPs resolvidos e volta a validar redirecionamentos. A ligação usa o IP validado para evitar uma segunda resolução DNS divergente.

## Testar

### Repetir uma fonte que falhou

No detalhe, usar **Repetir fonte** junto ao módulo elegível. Apenas esse módulo volta a executar. O backend verifica o dono, recusa uma investigação já em curso, aplica um máximo de seis novas tentativas por investigação/minuto e mantém as quotas dos fornecedores. Os módulos concluídos não têm este botão. As verificações técnicas exigem novamente confirmação de que o website é próprio ou autorizado, e só podem ser repetidas se já pertenciam à investigação inicial. O modo de demonstração não aceita novas tentativas.

Se a última consulta ficar incompleta, os resultados anteriores continuam visíveis com esse aviso. Se uma consulta concluída deixar de devolver uma evidência, esta passa para **Evidências de recolhas anteriores**. É excluída da contagem atual, da comparação e do contexto da nova IA; isto não prova que uma ameaça desapareceu. Um registo que reapareça recupera a identidade e deixa essa secção. A observação anterior não recebe artificialmente uma nova data de consulta.

Uma alteração das evidências ou da cobertura torna a síntese antiga desatualizada, mesmo que não apareçam novos indicadores. Usar **Atualizar síntese** antes de fazer perguntas. A atualização da IA é explícita para controlar chamadas e consumo. O PDF inclui os mesmos avisos. Sínteses da versão anterior, cujo fingerprint não incluía cobertura, também requerem atualização. Se as fontes mudarem enquanto a IA responde a uma pergunta, a resposta não é guardada como atual.

O endpoint é `POST /api/v1/investigations/{id}/retry`, com `provider` e, para verificações técnicas, `authorized: true`. Os valores de provider são definidos no schema da API. Uma investigação de mensagem repete consultas a partir dos links minimizados que guardou; o texto original não é recuperado. Se um reinício ocorrer antes de esses links terem sido extraídos, é necessário criar outra investigação com a mensagem.

Backend, a partir de `backend/`:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m pip_audit --cache-dir .cache/pip-audit
```

Os testes usam base própria e respostas controladas; não varrem terceiros. Cobrem acesso entre contas, hashes antigos/novos, tokens, migrações, SSRF/redirecionamentos, quotas, datas, fontes, referências da IA, mensagens e PDF. Existe um aviso de depreciação do TestClient sobre `httpx`; os testes passam, mas convém acompanhar a futura migração dessa dependência.

Frontend, a partir de `frontend/`:

```powershell
npm.cmd run build
npm.cmd audit
```

Com ambos os servidores ligados, a partir de `codigo/` e com Chrome instalado:

```powershell
node tests/browser.mjs
```

Atenção: tests/browser.mjs foi concebido para um backend de teste SEM chaves externas e assume esse estado. Não executar contra a instância atual com Tavily/Groq configuradas: iniciaria consultas reais e as suas asserções antigas sobre fontes sem acesso deixariam de ser válidas. Nesse ambiente isolado, cria uma conta sintética e duas investigações na base local. Requer CISA acessível ou cache válida. Produz screenshots, um PDF e um resumo em `test-results/`, todos ignorados. Usa um perfil isolado e não as sessões pessoais do Chrome. Não equivale a uma avaliação da qualidade do modelo real.

As versões diretas Python estão fixadas em `requirements*.txt`; `requirements-dev.lock.txt` regista o ambiente Windows/Python 3.12 validado. O frontend usa `package-lock.json`. O override PostCSS 8.5.23 corrige os avisos detetados sem uma migração maior do Next.js; rever ao atualizar Next.

## Limites desta entrega e próximo passo

Tavily e Groq já estão configuradas e autenticadas nesta máquina. Existe um dossiê real British Library e avaliação inicial com cinco casos fictícios, além de uma pergunta real no navegador. A suite passou 86 testes. URLhaus/PhishTank/HIBP continuam sem aceitação ao vivo; IntelX não está implementado. Consultar VALIDACAO_QUALIDADE_2026-10-21.md na pasta superior para os limites, incluindo falhas intermitentes de formato e quotas.

A execução em segundo plano é adequada à demonstração local, com duas tarefas em simultâneo. Após reinício, trabalhos incompletos e fontes em execução passam a interrompidos; os módulos elegíveis podem ser repetidos pelo utilizador. As observações anteriores são conservadas, mas ainda não existe um log imutável de cada alteração de conteúdo. SQLite, armazenamento do token no navegador, ausência de recuperação de conta e de um limite distribuído de login precisam de revisão antes de utilização pública. Não houve alojamento, domínio, publicação ou alteração do repositório remoto.

Consultar o roadmap v5 e `ESTADO.md` na pasta superior para os critérios ainda pendentes. Atribuições e requisitos exatos do docente aguardam confirmação.

## Avaliação de qualidade e cobertura

`backend/evaluations/cases.py` contém apenas cenários fictícios. `scripts/evaluate_ai.py` faz zero chamadas por defeito; `--live` autoriza chamadas ao modelo com esses dados e `--interval 30` espaça os casos. Não pesquisa Tavily nem cria incidentes no histórico. Guarda relatório, referências, número de pedidos e hash do prompt, sem chaves. Cada geração pode fazer até duas chamadas apenas se ocorrer a falha de JSON reconhecida; ambos os formatos têm a mesma validação local. Um erro de quota interrompe a avaliação.

O teste `node tests/source-coverage.mjs`, a partir de codigo/, verifica a instalação atual com Tavily/Groq configuradas: explica acessos opcionais, separa a extensão IntelX e verifica 390 px sem overflow. Cria apenas uma conta local sintética e não inicia análises externas.

A classificação OSINT exige uma menção delimitada ao domínio para apresentar uma referência candidata. Uma coincidência apenas pelo nome fica por verificar. Esta heurística reduz associações indevidas, mas não substitui validação humana.

## Revisão de 22/10/2026 - cobertura e agrupamento

A cobertura é calculada em coverage.py e apresentada separadamente da IA no site e no PDF. Sem evidência candidata do alvo, o modelo não é chamado; alertas gerais e referências por verificar continuam visíveis. O prompt analyst-v3 mantém IDs obrigatórios nas afirmações e permite listas de observações/recomendações vazias quando não há suporte. Se surgir evidência relevante depois, a geração volta a ficar elegível.

incident_groups.py agrupa apenas pela mesma ligação de origem ou por data estruturada de incidente/tipo/alvo. Os grupos são candidatos e podem conter incidentes diferentes; datas de publicação nunca preenchem event_at. Não usa LLM, não faz pesquisas adicionais e não altera a evidência original.

O formulário Configurar_APIs.cmd aceita agora URLhaus como terceiro campo opcional. Campos vazios preservam chaves existentes. Consultar CONFIGURAR_URLHAUS.md na pasta superior; a chave continua ausente nesta instalação. --live em verificar_ligacoes.py não faz consulta URLhaus e não a autentica.

A suite final passou 98 testes em 88,61 s, build passou e tests/coverage-flows.mjs validou a interface com dados controlados, zero pedidos externos e 390 px sem overflow. O teste usa respostas locais controladas, não equivale a uma investigação real.

Para uma janela autorizada de trabalho, WEBSECAI_REQUEST_WINDOW_FILE pode apontar para um JSON com deadline_utc, limits e baseline. O limite restritivo entra na mesma atualização atómica de provider_usage; não pode aumentar a quota normal. O utilitário de avaliação aceita --window-budget e a recuperação conta como outro pedido. Sem esse parâmetro, mantêm-se os limites normais. Não alterar .env para um orçamento temporário; usar apenas ambiente do processo e repor o arranque normal no fim.

Consultar VALIDACAO_NOTURNA_2026-10-22.md e GUIAO_DEMONSTRACAO.md. A password própria, o redesign e os gráficos/grafos continuam adiados.
