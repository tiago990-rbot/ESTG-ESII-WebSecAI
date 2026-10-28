# WebSecAI

Projeto académico de Engenharia de Software II.

## Participantes

- Pedro Mano
- Tiago Melo
- Gonçalo Cordeiro

## Descrição do projeto

O WebSecAI é uma aplicação web de apoio à análise da postura básica de segurança de websites e à investigação de ameaças através de fontes públicas.

A aplicação combina verificações técnicas, pesquisa pública e indicadores de ameaças, organizando os resultados em dossiês com evidências, datas, fontes e limitações. Integra também um módulo de inteligência artificial para produzir sínteses fundamentadas nos resultados recolhidos, sujeitas a revisão humana.

O projeto dispõe de uma versão publicada online, com autenticação individual, histórico por utilizador e autorização de acesso às investigações.

## Funcionalidades implementadas

### Verificações técnicas

- Verificações de DNS, HTTPS e certificados TLS.
- Análise de cabeçalhos HTTP de segurança.
- Verificação de atributos de cookies e determinados ficheiros públicos.
- Apresentação de resultados e evidências sobre a configuração observada.
- Execução apenas em websites próprios ou com autorização para teste.

### Investigação de ameaças e fontes públicas

- Investigação a partir de um domínio, link ou mensagem suspeita.
- Pesquisa de referências públicas através do Tavily.
- Consulta de indicadores de URLs associados a malware através do URLhaus.
- Consulta do catálogo CISA KEV para contexto geral sobre vulnerabilidades com exploração conhecida.
- Seleção explícita de fontes opcionais, dependentes de configuração e condições de acesso.
- Consulta do estado de cada módulo, distinguindo resultados, ausência de correspondências, erros e fontes não solicitadas.

### Organização e exploração dos resultados

- Dossiês individuais com evidências e identificação das fontes.
- Panorama da investigação e cobertura da recolha.
- Pesquisa e filtragem de evidências.
- Cronologia com distinção entre datas de publicação, incidente e consulta.
- Mapa de relações entre o dossiê, os módulos consultados e as evidências recolhidas.
- Separação dos alertas de contexto global das evidências específicas do alvo.
- Comparação entre recolhas quando existem resultados compatíveis.
- Revisão humana das evidências, com avaliações, notas e histórico.
- Atualização seletiva de módulos, sujeita aos limites de utilização.

### Contas e histórico

- Autenticação com contas individuais.
- Acesso limitado aos elementos autorizados na instalação online.
- Histórico de análises e investigações por utilizador.
- Autorização de acesso com base no proprietário dos dados.
- Convites privados para definição da palavra-passe.
- Alteração de palavra-passe e reposição através de token privado.

### Relatórios e demonstração

- Exportação dos dossiês para PDF.
- Inclusão de evidências, fontes, limitações, cronologia e mapa de relações nos relatórios.
- Demonstração com dados fictícios, sem consultas externas nem chamadas a modelos de IA.

## Papel da inteligência artificial

As verificações técnicas e os módulos de pesquisa recolhem os dados. A IA recebe informação estruturada para produzir uma síntese com referências às evidências, limitações e prioridades de análise.

A aplicação procura rejeitar respostas inválidas e preservar os resultados recolhidos quando a síntese falha. As conclusões produzidas pela IA exigem revisão humana e não substituem a validação das fontes.

O módulo utiliza a API Groq. Na última validação registada, em 24 de outubro de 2026, não produziu uma síntese válida, mantendo-se esse problema por diagnosticar.

## Integrações externas

| Serviço | Finalidade | Condições |
| --- | --- | --- |
| URLhaus | Consulta de registos de URLs associados a malware. | Requer Auth-Key e acesso aceite pelo fornecedor. |
| Tavily | Pesquisa de notícias, relatórios e outras referências públicas. | Requer chave e está sujeito a quotas. |
| Groq | Execução do modelo de IA para síntese das evidências. | Requer chave, modelo disponível e limites de utilização. |
| CISA KEV | Contexto geral sobre vulnerabilidades com exploração conhecida. | Catálogo público; não comprova um ataque ao alvo. |
| PhishTank | Consulta opcional de registos de phishing por URL. | Depende da configuração e das condições de acesso. |
| HIBP | Módulos opcionais de catálogo público de fugas e consulta de exposição. | Os módulos têm requisitos de acesso distintos. |
| urlscan | Pesquisa opcional de scans públicos existentes. | Não submete novos scans; depende de configuração e quotas. |

As fontes opcionais estão desligadas por predefinição. Intelligence X permanece uma extensão futura, sem integração ativa.

## Tecnologias utilizadas

- **Frontend:** Next.js, React, TypeScript/TSX e CSS.
- **Backend:** Python e FastAPI.
- **Persistência:** SQLAlchemy, com PostgreSQL na instalação online e suporte a SQLite para desenvolvimento local.
- **Migrações:** Alembic.
- **Inteligência artificial:** API Groq.
- **Pesquisa pública:** API Tavily.
- **Threat Intelligence:** URLhaus, CISA KEV e adaptadores opcionais.
- **Relatórios:** ReportLab para geração de PDFs.
- **Testes:** pytest no backend e verificações de compilação e integração da interface.
- **Versionamento:** Git e GitHub.

## Arquitetura e publicação

A instalação online utiliza três componentes principais:

| Componente | Serviço | Responsabilidade |
| --- | --- | --- |
| Interface web | Cloudflare | Disponibiliza a interface e os recursos utilizados pelo navegador. |
| API e processamento | Render | Executa o backend FastAPI, valida permissões, processa tarefas, consulta fornecedores e gera relatórios. |
| Base de dados | Neon | Guarda contas, análises, investigações, evidências e registos de controlo em PostgreSQL. |

O navegador comunica com a API, que consulta a base de dados e os serviços externos conforme a operação solicitada. As credenciais dos fornecedores permanecem no backend.

A publicação foi configurada nos planos gratuitos escolhidos pelo grupo. Existem quotas e possíveis atrasos no primeiro acesso após períodos de inatividade.

**Aplicação:** [WebSecAI online](https://websecai-frontend.websecai-estg.workers.dev/)

## Segurança, privacidade e limites

As verificações técnicas destinam-se exclusivamente a websites próprios ou autorizados. Não estão previstos exploração de vulnerabilidades, ataques de força bruta ou testes de carga.

As consultas de Threat Intelligence não visitam automaticamente os URLs suspeitos. O mapa de relações representa a proveniência da recolha, não causalidade, autoria ou confirmação de ataques.

Cada utilizador tem acesso às suas próprias investigações. Partilhar o endereço da aplicação não permite consultar os dados dos restantes elementos. Um espaço de investigação partilhado exige requisitos e permissões próprios.

Uma referência pública ou um indicador não prova uma intrusão. A ausência de correspondências também não comprova segurança. Os resultados não constituem uma auditoria completa nem uma certificação.

Palavras-passe, chaves de API, ligações privadas e bases de dados não devem ser incluídas no repositório ou nos pacotes partilhados.

## Estado do projeto

O projeto evoluiu da definição inicial para uma aplicação implementada e publicada.

Na última validação registada, em **24 de outubro de 2026**:

- A publicação do backend terminou com sucesso.
- URLhaus e Tavily responderam com sucesso numa investigação pública real.
- A síntese IA falhou, preservando as evidências e deixando o dossiê no estado Parcial.
- A geração de PDFs tinha sido validada localmente; a descarga na instalação online ainda não estava confirmada.

A existência de uma chave configurada não garante autenticação ou funcionamento do respetivo serviço. As integrações continuam sujeitas às permissões, quotas e disponibilidade dos fornecedores.

## WBS 

A WBS organiza os principais entregáveis e o trabalho de consolidação. Responsáveis e datas são acordados pelo grupo.

| Código | Entregável | Trabalho |
| --- | --- | --- |
| 1.1 | Definição e âmbito | Manter objetivos, limites e participantes atualizados. |
| 1.2 | Organização | Gerir código, tarefas, responsabilidades e entregas. |
| 2.1 | Requisitos | Consolidar funcionalidades e critérios de aceitação. |
| 2.2 | Casos de uso | Documentar autenticação, análises, investigações e relatórios. |
| 2.3 | Requisitos da IA | Definir entradas, referências, limitações e orçamento. |
| 3.1 | Arquitetura | Documentar frontend, API, base de dados e fornecedores. |
| 3.2 | Modelo de dados | Manter modelos, migrações e regras de autorização. |
| 3.3 | Interface | Validar usabilidade, acessibilidade e utilização em dispositivos móveis. |
| 4.1 | Verificações técnicas | Manter verificações e resultados estruturados. |
| 4.2 | Contas e histórico | Consolidar autenticação, convites, palavras-passe e isolamento dos dados. |
| 4.3 | Threat Intelligence | Validar integrações, estados das fontes, cache e quotas. |
| 4.4 | Exploração de evidências | Consolidar filtros, cronologia, mapa e comparação entre recolhas. |
| 4.5 | Inteligência artificial | Diagnosticar falhas e avaliar a qualidade das sínteses. |
| 4.6 | Revisão humana | Validar avaliações, notas e histórico das evidências. |
| 4.7 | Relatórios | Validar conteúdo, apresentação e descarga dos PDFs online. |
| 5.1 | Testes técnicos | Testar em ambientes próprios ou controlados. |
| 5.2 | Avaliação da IA | Comparar respostas com evidências e identificar afirmações sem suporte. |
| 5.3 | Integração e segurança | Validar fluxos, permissões, falhas e persistência. |
| 5.4 | Publicação | Acompanhar quotas, disponibilidade e procedimentos de rollback. |
| 6.1 | Documentação | Atualizar instruções de utilização, instalação e continuidade. |
| 6.2 | Entrega académica | Preparar demonstração, relatório e apresentação final. |

## Evolução futura

- Resolver e validar a síntese IA na instalação online.
- Concluir a validação dos fluxos com os três elementos do grupo.
- Consolidar a exportação PDF online e a avaliação de utilização.
- Avaliar um espaço de investigação partilhado, com permissões próprias.
- Avaliar uma integração MCP para consulta controlada de resultados por assistentes de IA.

A integração MCP permanece uma possibilidade futura e não faz parte das funcionalidades atualmente implementadas.em IA disponível. |
| 6.1 | Documentação | Preparar instruções de execução, utilização e limitações. |
| 6.2 | Entrega | Preparar demonstração e verificar requisitos do docente. |
