# Runner estático manual — WebSecAI

Não é chamado pelo FastAPI e não recebe pedidos públicos. Não executa o código recebido, scripts de instalação, hooks, builds ou testes. É um subprocesso de ferramentas fixas, **não uma sandbox de segurança**. Para código não confiável, usar um ambiente descartável isolado sem segredos, privilégios, rede interna ou acesso ao Docker do host. O grupo deve preparar esse ambiente antes de disponibilizar automação do runner.

Requisitos: Python/dependências do backend e o executável oficial da ferramenta escolhida. Semgrep CE requer ambiente compatível; preferir Linux/CI. As três regras locais de Semgrep são exemplos limitados, não uma política completa. Rever as licenças das ferramentas e das regras usadas; não assumir acesso gratuito a regras Pro.

Exemplo sobre **fixtures fictícias**, a partir da raiz do repositório, ajustando apenas os caminhos dos executáveis:

```text
python tools/security_lab/runner.py --source tools/security_lab/fixtures/vulnerable --tool gitleaks --engine CAMINHO/gitleaks.exe --out RESULTADOS/NOVA_PASTA --authorized
```

Substituir `--tool` por `semgrep` e `--engine` pelo seu executável para usar as regras locais; `osv` usa `osv-scanner scan source`. OSV necessita de `--allow-osv-network` porque pode consultar avisos externos a partir dos nomes/versões das dependências. Não se ativa análise de chamadas/compilação nem remediação automática. Essa autorização de rede é distinta de enviar código à IA.

O diretório de saída tem de ser novo/vazio e fora da origem. Não são sobrescritos resultados anteriores. As entradas são limitadas pelo mesmo contrato de ficheiros do site. Pastas de dependências/controlo de versões são ignoradas, links rejeitados. O motor recebe cópias temporárias do código original para conseguir detetar segredos; usar apenas código que se tem autoridade para analisar. As credenciais do ambiente da aplicação não são herdadas pelo subprocesso.

Timeout de 90 segundos, limite de relatório/stdout de 1 MB, término da árvore de processos no timeout. Não é um limite rígido de memória/CPU do sistema: aplicar esses limites no container/VM/CI. Não há hooks, execuções shell ou download de regras por URL. A instalação do motor é feita pelo responsável, verificando origem, versão e checksum publicados.

Saídas:

- `report.json`: relatório nativo mínimo, sanitizado, para importar no site. Valores Gitleaks e metadata arbitrária são descartados.
- `import_payload.json`: contrato `tool`, `version`, `source_digest`, `report_json`; pode ser enviado ao endpoint autenticado `/api/v1/lab/{id}/imports`, em ambiente do grupo autorizado. O runner não conhece nem usa o token da aplicação.
- `manifest.json`: hash do executável, digest da revisão, código de saída, número de achados e limitações. A versão textual deve ser confirmada pelo responsável; não é deduzida pelo nome do ficheiro.

Enviar ao site os mesmos ficheiros originais usados pelo runner: o digest é calculado antes da redação. Comparar com o digest apresentado no dossiê. JSON/SARIF de outra revisão é rejeitado quando os digests divergem. A importação continua a ser uma declaração do utilizador, não uma assinatura/atestado do runner.

Validação observada: Gitleaks oficial 8.30.1, arquivo Windows x64 SHA-256 `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`; executável `17157e2ee8b76fc8b1d8bee607a250e34b8a8023c8bc81822d4b5ee4d78fcb7c`. Fixture vulnerável: um marcador sintético `WSAI_FIXTURE_...`; corrigida: zero. Não se executaram as funções Python das fixtures. Não foi feita qualquer chamada a um alvo externo ou ao modelo.

Semgrep e OSV: adaptadores testados com fixtures; execução real pendente. O pacote não inclui executáveis, caches, relatórios brutos, chaves ou dependências instaladas. Não anunciar scans reais destas ferramentas com base nos exemplos de importação.
