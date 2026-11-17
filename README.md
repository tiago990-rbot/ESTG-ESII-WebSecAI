# WebSecAI

Projeto académico de Engenharia de Software II.

## Participantes

- Pedro Mano
- Tiago Melo
- Gonçalo Cordeiro

## O projeto

Aplicação web de apoio à análise da postura de segurança de websites e à investigação de referências públicas e indicadores de ameaças. Organiza resultados, evidências e limitações num histórico por utilizador, com exportação PDF.

As verificações técnicas destinam-se apenas a websites próprios ou autorizados. As consultas de Threat Intelligence não visitam automaticamente os URLs suspeitos. Ausência de correspondências não prova segurança e os resultados não constituem certificação nem prova de intrusão.

## Funcionalidades

- Contas, autenticação, histórico individual e autorização por dono.
- Verificações DNS, HTTPS/TLS, cabeçalhos HTTP, cookies e ficheiros públicos, mediante autorização.
- Investigação por domínio/link ou mensagem, evidências por fonte e comparação entre recolhas.
- Relatórios PDF e repetição seletiva de fontes com falhas ou cobertura incompleta.
- Demonstração com dados fictícios e sem consultas externas.
- Adaptadores de Threat Intelligence e pesquisa pública, dependentes de configuração e acesso do fornecedor.
- Síntese e perguntas apoiadas por IA, com referências a evidências e rejeição de saídas inválidas.

As chaves externas são opcionais por módulo. A interface distingue configuração, consultas observadas e bloqueios de quota; configurar não comprova aceitação ao vivo. Há mapas de relações, cronologia e gráficos nas investigações/PDFs, além de alteração/ativação/recuperação das passwords das contas. Uma funcionalidade de verificar passwords em fugas e um servidor MCP próprio continuam por implementar.

## Incrementos locais de 30/10/2026

- `/usage`: limites internos partilhados, reservas, renovação, observações seguras de limites externos e exceções administrativas +1 com auditoria. Consulta opcional de saldo Tavily exige opt-in e ação administrativa distinta.
- `/security-lab`: revisão estática de código autorizado, importação Semgrep/OSV/Gitleaks, revisão independente do código por IA, correlação separada de achados, revisão humana e PDF com visuais. Desativado por defeito até configurar `SECURITY_LAB_ENABLED`.
- `tools/security_lab`: runner manual separado e fixtures fictícias. Não executa código recebido nem funciona como serviço público/sandbox.

Consultar [o guia de integração](docs/CONTINUAR_AQUI_2026-10-30.md), [a validação local](docs/VALIDACAO_LOCAL_2026-10-30.md) e [o texto de passagem ao colega](docs/MENSAGEM_PARA_GPT_COLEGA_2026-10-30.md). Estes incrementos não foram publicados nesta sessão. Limites externos em falta permanecem desconhecidos; outras aplicações e quotas do alojamento exigem consulta do responsável. Nenhum pagamento, push ou teste ativo público foi efetuado.

## Tecnologias e estrutura

FastAPI/Python, SQLAlchemy e Alembic no backend; Next.js, React e TypeScript na interface; ReportLab nos PDFs. SQLite mantém-se para desenvolvimento local e PostgreSQL está preparado para a instalação online.

| Caminho | Conteúdo |
| --- | --- |
| `codigo/backend` | API, modelos, migrações e testes |
| `codigo/frontend` | Interface e adaptador Cloudflare |
| `codigo/docs` | Documentação académica recebida |
| `scripts/configurar_apis.ps1` | Formulário Windows com campos ocultos |
| `docs` | Proveniência, README inicial e relatórios de validação |
| `render.yaml` | Um serviço Render Free, sem deploy automático |

## Executar localmente

Pré-requisitos: Python 3.12 e Node.js 22/24 com npm. No Windows, a partir da raiz do repositório:

```powershell
cd codigo/backend
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
& .\.venv\Scripts\python.exe scripts/setup_local.py
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Num segundo terminal:

```powershell
cd codigo/frontend
npm.cmd ci
if (-not (Test-Path -LiteralPath .env.local)) { Copy-Item .env.example .env.local }
npm.cmd run dev
```

Abrir `http://127.0.0.1:3000`, criar uma conta local e escolher **Experimentar demonstração**. A configuração local gera um segredo aleatório sem o apresentar. Não enviar `.env`, bases ou chaves para o Git.

Para configurar URLhaus, abrir `codigo/Configurar_APIs.cmd` e introduzir a Auth-Key pessoalmente no campo oculto. Tavily/Groq não são necessárias para o teste isolado URLhaus. Consultar [a validação URLhaus](docs/VALIDACAO_URLHAUS.md) antes de efetuar pedidos reais.

## Testes e publicação

Backend: `python -m pytest -q` no ambiente virtual. Frontend: `npm run build`. Os testes de fornecedores usam respostas controladas; não comprovam autenticação real.

O alojamento escolhido é **Neon Free + Render Free para a API + Cloudflare Free para a interface**, com subdomínios gratuitos. Criar contas nos fornecedores não significa que a app esteja publicada. Os segredos ficam no backend e são configurados pela pessoa nos painéis. Não colocar ligações PostgreSQL ou chaves em `NEXT_PUBLIC_*`.

Na instalação online, o registo público fica fechado e as três contas do grupo são provisionadas privadamente. O histórico continua separado por dono. A app comum não cria automaticamente um espaço de investigação partilhado.

Ver [validação e publicação](docs/VALIDACAO_PUBLICACAO.md) para o estado efetivo, quotas, testes remotos pendentes, cold starts e rollback.

## Origem e evolução

O código desta evolução parte do ZIP `WebSecAI_Continuacao_2026-10-22_v2.zip` fornecido pelo grupo. O GitHub continha apenas o README inicial; não foi usado como base presumida da aplicação. O [README anterior](docs/README_INICIAL_GITHUB.md) e o histórico foram preservados. O [manifesto original](docs/MANIFEST_SHA256.json) identifica o snapshot recebido.
