# Casos de Uso — WebSec Check

## Atores
- Visitante
- Utilizador autenticado

## Casos de uso principais
- Registar utilizador
- Autenticar utilizador
- Terminar sessão
- Submeter website para análise
- Consultar resultado da análise
- Consultar histórico pessoal
- Consultar detalhe de análise anterior

## Diagrama simplificado

```mermaid
flowchart TD
    V[Visitante] --> UC1[Registar utilizador]
    V --> UC2[Iniciar sessão]

    U[Utilizador autenticado] --> UC3[Terminar sessão]
    U --> UC4[Submeter URL para análise]
    U --> UC5[Consultar resultado da análise]
    U --> UC6[Consultar histórico]
    U --> UC7[Consultar detalhe de análise]

    UC4 --> UC5
    UC6 --> UC7
