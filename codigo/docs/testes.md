# Testes — WebSec Check

## Testes unitários previstos
- validação de registo de utilizador
- validação de login
- criação de análise
- cálculo do score
- associação de análise ao utilizador
- listagem do histórico
- abertura de detalhe de análise

## Testes de aceitação baseados em user stories

### TA01 — Registo
Dado um visitante sem conta,
quando preencher username, email e password válidos,
então o sistema deve criar a conta com sucesso.

### TA02 — Login
Dado um utilizador registado,
quando inserir credenciais corretas,
então o sistema deve permitir acesso à área autenticada.

### TA03 — Criar análise
Dado um utilizador autenticado,
quando submeter um URL válido,
então o sistema deve mostrar o resultado da análise e guardar o registo.

### TA04 — Ver histórico
Dado um utilizador com análises guardadas,
quando abrir a página de histórico,
então deve ver a lista das suas análises anteriores.

### TA05 — Ver detalhe
Dado um utilizador com histórico,
quando abrir uma análise antiga,
então deve conseguir ver findings e detalhes técnicos.
