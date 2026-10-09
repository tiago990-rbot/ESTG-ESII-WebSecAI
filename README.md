# WebSec AI

Projeto académico de Engenharia de Software II — ESTG.

## Participantes

- Pedro Mano
- Tiago Melo
- Gonçalo Cordeiro

## Descrição do projeto

O WebSec AI pretende ser uma aplicação web de apoio à análise não intrusiva da postura básica de segurança de websites. Permitirá consultar verificações técnicas e compreender os resultados através de explicações e sugestões apoiadas por inteligência artificial.

O projeto está na fase de definição. As funcionalidades seguintes são propostas iniciais a validar pelo grupo e com o docente, ainda não implementadas.

## Âmbito inicial proposto

- Verificações de DNS, HTTPS e certificados TLS.
- Verificações de cabeçalhos HTTP de segurança e atributos de cookies.
- Painel de resultados com evidências e recomendações.
- Registo, autenticação e histórico por utilizador.
- Exportação de relatórios.
- IA para explicar resultados técnicos em linguagem simples e sugerir prioridades de melhoria.

### Papel da IA

As verificações técnicas recolherão os dados. A IA receberá resultados estruturados para produzir explicações e sugestões associadas às evidências e sujeitas a validação. Modelo, fornecedor e custos serão definidos no levantamento de requisitos.

### Limites

As análises destinam-se a websites próprios ou com autorização para teste. Não estão previstos exploração de vulnerabilidades, ataques de força bruta ou testes de carga. Os resultados não constituem uma certificação de segurança.

## Referência

Projeto inspirado no WebSec Check, fornecido ao grupo em ZIP: https://github.com/MRDACC/Engenharia_Software_Websec-Check

O projeto de referência utiliza FastAPI, Next.js e SQLite. As tecnologias do WebSec AI serão decididas pelo grupo. Este repositório contém a definição inicial; eventual reutilização de código deverá confirmar a licença e identificar a origem.

## WBS inicial

A WBS divide o trabalho em entregáveis e tarefas. Responsáveis e datas serão acordados pelo grupo no GitHub Project.

| Código | Entregável | Trabalho previsto |
| --- | --- | --- |
| 1.1 | Definição | Confirmar objetivos, âmbito e participantes. |
| 1.2 | Organização | Criar repositório e Project; definir tarefas e responsáveis. |
| 2.1 | Requisitos | Identificar funcionalidades e critérios de aceitação. |
| 2.2 | Casos de uso | Documentar autenticação, análise e consulta de resultados. |
| 2.3 | Requisitos da IA | Definir entradas, respostas esperadas, limitações e orçamento. |
| 3.1 | Arquitetura | Escolher tecnologias, componentes e integrações. |
| 3.2 | Modelo de dados | Desenhar utilizadores, análises e resultados. |
| 3.3 | Protótipos | Desenhar e validar os principais ecrãs. |
| 4.1 | Verificações | Implementar verificações técnicas e resultados estruturados. |
| 4.2 | Contas e histórico | Implementar autenticação, persistência e permissões. |
| 4.3 | Interface | Implementar pedido de análise, painel e histórico. |
| 4.4 | IA | Implementar explicações baseadas nos resultados e tratamento de falhas. |
| 4.5 | Relatórios | Implementar exportação dos resultados. |
| 5.1 | Testes técnicos | Validar verificações em websites de teste controlados. |
| 5.2 | Avaliação da IA | Comparar explicações com evidências e identificar erros. |
| 5.3 | Integração | Validar fluxos, permissões e funcionamento sem IA disponível. |
| 6.1 | Documentação | Preparar instruções de execução, utilização e limitações. |
| 6.2 | Entrega | Preparar demonstração e verificar requisitos do docente. |

## Planeamento

O GitHub Project terá o mesmo nome do repositório: ESTG-ESII-WebSecAI. Cada tarefa deverá identificar o código WBS, descrição, critérios de conclusão, responsável e prazo acordado.
