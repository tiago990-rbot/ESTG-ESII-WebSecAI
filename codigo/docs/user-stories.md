# User Stories — WebSec Check

## Epic 1 — Autenticação
### US01
Como visitante, quero criar uma conta para poder guardar o meu histórico de análises.

*Critérios de aceitação*
- O sistema deve permitir registo com username, email e password.
- O username deve ser único.
- O email deve ser único.
- A password deve ser guardada de forma segura.

### US02
Como utilizador, quero iniciar sessão para aceder à minha área pessoal.

*Critérios de aceitação*
- O sistema deve validar credenciais.
- Em caso de sucesso, o utilizador entra na área autenticada.
- Em caso de erro, deve ser apresentada mensagem apropriada.

### US03
Como utilizador, quero terminar sessão para proteger o acesso à minha conta.

*Critérios de aceitação*
- O sistema deve permitir logout.
- Após logout, o utilizador deixa de aceder a páginas protegidas.

## Epic 2 — Análise de websites
### US04
Como utilizador autenticado, quero introduzir um URL/domínio para obter uma análise básica de segurança.

*Critérios de aceitação*
- O sistema deve validar o URL/domínio.
- O sistema deve executar a análise.
- O sistema deve devolver score, findings e detalhes técnicos.

### US05
Como utilizador, quero ver informações de DNS/IP do website analisado.

### US06
Como utilizador, quero ver o estado de HTTPS/TLS e do certificado.

### US07
Como utilizador, quero ver os headers de segurança do website.

### US08
Como utilizador, quero ver informações sobre cookies relevantes para segurança.

### US09
Como utilizador, quero saber se existem ficheiros públicos como robots.txt e sitemap.xml.

## Epic 3 — Histórico
### US10
Como utilizador, quero que as minhas análises fiquem guardadas para poder consultá-las mais tarde.

*Critérios de aceitação*
- Cada análise deve ficar associada ao utilizador autenticado.
- Devem ser guardados data/hora, URL, score e findings.

### US11
Como utilizador, quero consultar o meu histórico de pesquisas.

*Critérios de aceitação*
- O sistema deve listar análises do utilizador autenticado.
- Cada item deve mostrar data/hora, URL e score.

### US12
Como utilizador, quero abrir uma análise anterior para ver os detalhes completos.

*Critérios de aceitação*
- O sistema deve mostrar findings e resultados técnicos da análise escolhida.
