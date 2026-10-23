---
# Modelo de Classes — WebSec Check

## Classes principais
- User
- Scan
- Finding

## Descrição
A classe `User` representa o utilizador do sistema.
A classe `Scan` representa uma análise feita por um utilizador.
A classe `Finding` representa um problema ou observação identificado numa análise.

## Diagrama de classes

mermaid
classDiagram
    class User {
        +int id
        +string username
        +string email
        +string password_hash
        +datetime created_at
    }

    class Scan {
        +int id
        +int user_id
        +string url
        +string domain
        +datetime created_at
        +int score
        +string risk_level
        +string summary
        +json details_json
    }

    class Finding {
        +int id
        +int scan_id
        +string title
        +string severity
        +string category
        +string description
        +string recommendation
    }

    User "1" --> "0..*" Scan : possui
    Scan "1" --> "0..*" Finding : contém
