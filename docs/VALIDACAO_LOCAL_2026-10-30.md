# Evidência de validação local — 30/10/2026

Base pública: e55b8f919ac25dfc59e253bb47be03d83b91efb7. Código desenvolvido em checkout novo, sem copiar `.env`, bases de dados, contas ou chaves anteriores. Sem push, publicação ou alterações nos serviços do grupo.

## Backend

Python 3.12.14 no ambiente existente, executado a partir do checkout novo. SQLite exclusivo por execução da suite, nomes aleatórios em `.cache/tests`. A fixture apaga/cria **apenas** essa base dedicada; não se usou PostgreSQL ou Neon.

- Base antes das alterações: **174 aprovados, 1 omitido**.
- Suite completa após os incrementos: **208 aprovados, 1 omitido**. O omitido exige PostgreSQL real para provar tipos; não é uma aprovação PostgreSQL.
- Regressões finais focadas (quotas e Security Lab), após preservar resultados anteriores e disponibilizar histórico sob pedido: **37 testes distintos aprovados**. A fixture também desativa explicitamente flags novas para não herdar configuração privada da máquina.
- As novas datas foram revistas para produzir TIMESTAMP WITH TIME ZONE em PostgreSQL. O DDL gerado foi verificado sem ligação à base; isso não substitui a aceitação PostgreSQL real. O lote A foi ainda extraído do seu snapshot próprio, sem os ficheiros Lab, para validar a sua independência.

Dois avisos de depreciação na suite completa: integração FastAPI/Starlette TestClient com httpx e adaptador datetime SQLite numa prova de esquema antigo. Sem falhas nesses testes.

Cobertura relevante: concorrência de reservas e de exceções, papel administrativo no backend, idempotência, renovação UTC, janela privada e de aceitação, tetos independentes, Retry-After/saldo observado, headers/metadata permitidos, Tavily usage simulado, respostas sem dados, controlo por dono, referências inválidas de IA, JSON/SARIF, ZIP/caminhos/limites/corpo chunked, segredo sintético redigido, ausência de repetições, revisão humana concorrente, síntese desatualizada, PDF sem novas chamadas e cancelamento/histórico conservado.

Tavily/Groq/URLhaus reais: **nenhuma nova chamada nesta implementação**. As respostas dos testes são fictícias. Não se mediu qualidade real de raciocínio, latência, cobertura, saldo da conta ou disponibilidade de modelos.

## Frontend e bundle

`npm ci --ignore-scripts` com o lockfile existente, sem alterar versões ou ativar serviços. `npm run build` aprovado com verificação TypeScript e novas rotas `/usage`, `/security-lab` e `/security-lab/[id]`.

Build OpenNext/Cloudflare aprovado localmente, gerando `.open-next/worker.js`. O primeiro ensaio na sandbox falhou por acesso a diretórios do Windows; o ensaio de compilação com o acesso local necessário passou. OpenNext avisa que Windows não tem compatibilidade integral; o colega deve compilar/validar no seu ambiente compatível. Compilar não publica nem demonstra o runtime Cloudflare.

Build de pré-visualização usou explicitamente API `http://127.0.0.1:8002` e `WEBSECAI_LOCAL_PREVIEW=1`. Não publicar esse bundle. A publicação deve reconstruir com o URL HTTPS correto. Artefactos instalados/builds não vão no pacote.

## Motores estáticos

Gitleaks oficial 8.30.1, arquivo validado pelo SHA-256 publicado. Execução separada nas fixtures versionadas:

| Fixture | Resultado observado | O que demonstra |
| --- | --- | --- |
| `vulnerable/app.py` | 1 achado, exit code 10 | Padrão de marcador intencional detetado pelo motor, importação e redação |
| `fixed/app.py` | 0 achados, exit code 0 | Marcador ausente nesta fixture; não é certificação geral |

As funções das fixtures não foram executadas. Não houve alvo externo, tentativa de intrusão ou uso de uma credencial. Após melhorar o timeout/limite de saída do runner, repetiram-se os dois casos em pastas novas, preservando os primeiros resultados.

Semgrep/OSV: normalização JSON/SARIF validada com fixtures; **motores reais não executados**. Regras Semgrep locais são exemplos e precisam de validação real no ambiente escolhido. Não foi instalado Docker nem alterada virtualização/WSL. O runner nativo manual não substitui uma sandbox de SO para código não confiável.

## PDF e interface

Exemplo fictício de três páginas: cabeçalho/olho WebSecAI, síntese ilustrativa, barras por origem, cronologia de registos, mapa de localização, correlações/prioridades, achados e inventário. Renderizado com Poppler e as três páginas inspecionadas visualmente. Os textos IA estão identificados como **simulados**, sem modelo real. Dois avisos de fontes genéricas do Poppler não produziram defeitos nas páginas inspecionadas.

A ferramenta de Computer Use interrompeu a verificação porque não conseguiu determinar o URL do navegador com confiança suficiente. A automação de UI foi parada, sem contornar a proteção. Portanto, **o percurso visual no browser, responsividade e aceitação desktop/mobile não estão validados**. Não existe captura de aceitação do frontend novo.

Foi preparada apenas uma base local fictícia de pré-visualização, independente das bases anteriores. Não foi usado o login real do utilizador nem contornada a criação interna de contas online.

## O que falta ao responsável

Rever a base publicada/diferenças, ensaiar migrações e recuperação PostgreSQL, configurar papéis/opt-ins e planos gratuitos, preparar Semgrep/OSV reais num runner isolado, aceitar o modelo real dentro de um orçamento explícito, publicar de forma revista e confirmar o fluxo das três contas no navegador. Nenhuma destas aceitações é substituída pelos testes locais acima.

Os patches e hashes são verificados pelo manifesto exterior. A verificação local de aplicação de patches usa um índice Git temporário sobre a base identificada; não altera a árvore de trabalho nem dados privados. O código antigo e os originais estão preservados.
