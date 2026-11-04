# WebSecAI

Aplicação académica de **Engenharia de Software II** para análise da postura de segurança de websites e investigação de ameaças com fontes públicas.

**Equipa:** Pedro Mano, Tiago Melo e Gonçalo Cordeiro  

## O que faz a aplicação?

O WebSecAI reúne dados sobre um domínio, URL ou mensagem suspeita num dossiê com evidências, fontes, datas e limitações. O utilizador pode explorar os resultados, revê-los e exportá-los para PDF.

| Funcionalidade | O que permite fazer |
| --- | --- |
| **Análise técnica** | Verificar DNS, HTTPS/TLS, certificados, cabeçalhos HTTP, cookies e determinados ficheiros públicos, em websites próprios ou autorizados. |
| **Investigação pública** | Pesquisar referências e indicadores sobre domínios, links ou mensagens sem executar verificações técnicas ao alvo. |
| **Exploração de evidências** | Pesquisar e filtrar referências por fonte e contexto, consultar a cronologia, percorrer o mapa de proveniência e distinguir alertas gerais de evidências do alvo. |
| **Revisão humana** | Registar avaliações e notas, consultar o histórico de revisões e comparar recolhas compatíveis. |
| **Assistente IA** | Consultar sínteses e fazer perguntas sobre o dossiê quando a integração está disponível. As respostas referenciam evidências e exigem revisão humana. |
| **Relatórios e demonstração** | Exportar análises e dossiês para PDF ou explorar um exemplo fictício sem chamadas a fornecedores externos. |

O mapa mostra a origem das evidências. Uma referência não demonstra uma intrusão; a ausência de correspondências também não comprova que o alvo é seguro.

## Como utilizar

1. Entrar com a conta individual autorizada.
2. Abrir **Investigar** e escolher um domínio, link ou mensagem. Para experimentar sem consumir quotas externas, selecionar **Explorar demonstração**.
3. Escolher **Investigação pública** para recolher referências. Usar o modo com análise técnica apenas quando existir autorização para testar o website.
4. Abrir **Fontes** para confirmar o que foi consultado e distinguir resultados, ausência de correspondências e erros.
5. Explorar e rever as evidências. Exportar o PDF quando necessário.

O registo público está fechado na instalação online. O responsável envia um convite privado de uso único para cada pessoa definir a própria palavra-passe. A aplicação também permite alterar a palavra-passe e repô-la por link privado, sem envio automático de email. Cada conta tem o seu próprio histórico.

## Arquitetura

| Componente | Tecnologia | Responsabilidade |
| --- | --- | --- |
| Interface | Next.js, React, TypeScript e CSS · Cloudflare | Apresenta os formulários, dossiês e resultados. |
| API | Python e FastAPI · Render | Valida acessos, executa verificações e investigações, consulta fornecedores e gera PDFs com ReportLab. |
| Dados | PostgreSQL · Neon | Guarda contas, análises, investigações, evidências e revisões. |
| Desenvolvimento | SQLite, SQLAlchemy, Alembic e pytest | Suporta execução local, migrações e testes automatizados. |

O navegador comunica com a API. É a API que acede à base de dados e aos fornecedores. As chaves e credenciais são configuradas no backend.

## Fontes externas

- **URLhaus:** consulta de registos de URLs associados a malware.
- **Tavily:** pesquisa de notícias, relatórios e outras referências públicas.
- **CISA KEV:** alertas gerais de vulnerabilidades com exploração conhecida, apresentados separadamente.
- **Groq:** síntese e perguntas sobre as evidências.
- **PhishTank, HIBP e urlscan:** fontes opcionais, desligadas por predefinição e dependentes de configuração e acesso. A integração urlscan pesquisa scans existentes.

## Estado da validação

O alojamento foi publicado com os planos gratuitos escolhidos pelo grupo. O primeiro pedido após inatividade do backend pode demorar. As quotas de fornecedores são partilhadas pela instalação.

Na última validação registada, em **24/10/2026**, URLhaus e Tavily responderam com sucesso numa investigação pública. O Groq não produziu uma síntese válida; o dossiê ficou parcial e preservou as evidências. A geração de PDF foi validada localmente, mas a descarga online não ficou confirmada nessa validação.

As quotas locais registadas eram **200 pedidos Tavily por mês** e **10 chamadas Groq por dia**. A aceitação inicial aplicava ainda um limite adicional de duas consultas por fornecedor, incluindo tentativas, enquanto essa proteção estivesse ativa.

## Documentação e evolução

- **Casos de uso:** atores, pré-condições, fluxos e alternativas.
- **User stories:** necessidades dos utilizadores, critérios de aceitação e ligação aos casos de uso.
- **Kanban:** trabalho organizado por semana, com testes, commits ou documentos como evidência de conclusão.

Os documentos académicos destinam-se à pasta codigo/docs/. O código da interface está em codigo/frontend/ e o da API em codigo/backend/.

O laboratório de segurança, a colaboração em dossiês partilhados e a integração MCP são propostas futuras. O WebSecAI destina-se à análise académica e não substitui uma auditoria de segurança.

*README revisto em 04/11/2026 com base no código integrado e nos registos disponíveis. A revisão da documentação não constitui um novo teste da instalação online.*
