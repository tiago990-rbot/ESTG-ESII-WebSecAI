# PRD — WebSec AI

## 1. Visão geral

O WebSec AI é uma aplicação web que analisa, sem intrusão, a postura básica de segurança de um website e explica os resultados com apoio de inteligência artificial. Este PRD define o produto na fase de definição do projeto de Engenharia de Software II (ESTG), pelo que todas as funcionalidades são propostas a validar pelo grupo e pelo docente.

**Equipa:** Pedro Mano, Tiago Melo, Gonçalo Cordeiro. **Repositório e GitHub Project:** ESTG-ESII-WebSecAI.

### Problema

Quem gere um website pequeno ou académico raramente sabe se o DNS, o HTTPS, os certificados TLS, os cabeçalhos HTTP de segurança e as cookies estão bem configurados. As ferramentas existentes devolvem listas técnicas difíceis de interpretar e sem indicação clara do que corrigir.

### Proposta de valor

- Verificações técnicas determinísticas e não intrusivas, com evidências visíveis.
- Explicações e sugestões em linguagem acessível, geradas por IA a partir dos resultados estruturados e ligadas às evidências.
- Histórico por utilizador e relatórios exportáveis para acompanhar a evolução.

### Objetivos

1. Permitir que um utilizador autenticado peça uma análise de um website próprio ou autorizado e consulte os resultados num painel.
2. Apresentar cada resultado com evidência e recomendação.
3. Manter o produto utilizável quando a IA falha ou não está disponível.
4. Entregar, no fim do semestre, uma demonstração funcional, documentação e uma avaliação crítica da qualidade das explicações da IA.

## 2. Utilizadores-alvo

O produto serve quem é responsável por websites próprios ou para os quais tem autorização de teste. As personas abaixo são hipóteses a validar.

| Persona | Necessidade principal | O que espera do produto |
| --- | --- | --- |
| Estudante ou programador independente | Perceber se o seu projeto web tem falhas básicas de configuração | Resultados claros e passos concretos de correção |
| Responsável por site de pequena organização | Ter uma visão simples do estado de segurança, sem conhecimentos técnicos | Explicações em linguagem acessível e relatório para partilhar |
| Docente ou avaliador | Verificar funcionalidades, limites e qualidade da IA | Evidências rastreáveis e comportamento previsível |
| Assistente de IA (via MCP, opcional) | Consultar resultados e histórico em nome do utilizador | Acesso estruturado, autenticado e só de leitura |

## 3. Âmbito

O âmbito inicial cobre verificações passivas e a camada de explicação por IA; qualquer atividade ofensiva fica excluída.

### Dentro do âmbito (proposto)

- Verificações de DNS, HTTPS e certificados TLS.
- Verificações de cabeçalhos HTTP de segurança e atributos de cookies.
- Painel de resultados com evidências e recomendações.
- Registo, autenticação e histórico por utilizador.
- Exportação de relatórios.
- Explicações e sugestões geradas por IA a partir de resultados estruturados.

### Opcional, a decidir com o docente

- Integração de um servidor MCP para que assistentes de IA consultem resultados e histórico.

### Fora do âmbito

- Exploração de vulnerabilidades.
- Ataques de força bruta.
- Testes de carga.
- Análise de websites sem autorização do titular.
- Certificação de segurança: os resultados são indicativos e não constituem certificação.

## 4. Requisitos funcionais

Prioridades propostas: **Must** (essencial para a entrega), **Should** (desejável), **Could** (opcional). A coluna WBS liga cada requisito ao plano de trabalho.

| ID | Requisito | Critério de aceitação | Prioridade | WBS |
| --- | --- | --- | --- | --- |
| RF01 | Registo e autenticação de utilizadores | Um utilizador cria conta, inicia e termina sessão; palavras-passe nunca guardadas em texto simples | Must | 4.2 |
| RF02 | Pedido de análise de um URL | O utilizador submete um URL e confirma ter autorização; URLs inválidos são rejeitados com mensagem clara | Must | 4.3 |
| RF03 | Verificação de DNS | Resultado estruturado com registos relevantes e estado por verificação | Must | 4.1 |
| RF04 | Verificação de HTTPS e certificados TLS | Resultado com validade do certificado, cadeia, protocolo e redirecionamento HTTP→HTTPS | Must | 4.1 |
| RF05 | Verificação de cabeçalhos HTTP de segurança | Cada cabeçalho avaliado como presente, ausente ou mal configurado, com o valor observado | Must | 4.1 |
| RF06 | Verificação de atributos de cookies | Cookies avaliadas quanto a Secure, HttpOnly e SameSite, com evidência | Must | 4.1 |
| RF07 | Painel de resultados | Cada resultado mostra estado, evidência e recomendação | Must | 4.3 |
| RF08 | Histórico de análises por utilizador | O utilizador vê apenas as suas análises, ordenadas por data, e abre qualquer uma delas | Must | 4.2 |
| RF09 | Explicações e sugestões por IA | Cada resultado tem explicação associada à evidência, marcada como gerada por IA | Must | 4.4 |
| RF10 | Funcionamento sem IA | Se a IA falhar, o painel mostra os resultados técnicos e uma mensagem de indisponibilidade | Must | 4.4, 5.3 |
| RF11 | Exportação de relatórios | Exportação de uma análise num formato a definir (por exemplo PDF ou Markdown) com evidências e limitações | Should | 4.5 |
| RF12 | Comparação entre análises do mesmo site | O utilizador vê o que mudou entre duas análises | Could | 4.3 |
| RF13 | Servidor MCP só de leitura | Um assistente autenticado consulta resultados e histórico do utilizador, sem iniciar análises | Could | 3.1, 4.x |

## 5. Requisitos da IA

A IA explica e sugere; nunca recolhe dados nem decide o estado de uma verificação. As verificações técnicas produzem os dados e a IA recebe apenas resultados estruturados. Modelo, fornecedor e custos ficam por definir no levantamento de requisitos (WBS 2.3).

| Aspeto | Requisito proposto |
| --- | --- |
| Entrada | Resultados estruturados de cada verificação (identificador, estado, evidência observada, valor esperado). Sem páginas completas nem dados pessoais do utilizador |
| Saída | Por resultado: explicação curta, impacto possível, sugestão de correção e referência à evidência usada |
| Ligação às evidências | Cada afirmação aponta para a evidência que a suporta; afirmações sem evidência são descartadas ou assinaladas |
| Validação | Verificação automática do formato da resposta e rotina de revisão manual na fase 5.2 |
| Transparência | Todo o texto gerado é identificado como gerado por IA e acompanhado do aviso de que não é certificação |
| Falhas | Tempo limite, erro do fornecedor ou resposta inválida: o painel mostra os resultados técnicos sem explicação e permite repetir o pedido |
| Orçamento | Limite de custo por análise e por utilizador, a definir; pedidos acima do limite são recusados com mensagem |
| Privacidade | Só se envia ao fornecedor o necessário; o fornecedor e o tratamento dos dados são documentados |
| Avaliação | Comparar explicações com as evidências num conjunto de websites de teste e registar erros e alucinações (WBS 5.2) |

## 6. Requisitos não funcionais e limites

O produto só pode ser usado de forma responsável se as análises forem passivas, autorizadas e limitadas em ritmo. Os valores numéricos abaixo são propostas a confirmar.

### Requisitos não funcionais

- **Não intrusão:** apenas pedidos normais de leitura (resolução DNS, ligação TLS, pedidos HTTP GET ou HEAD); sem payloads de ataque, sem tentativas de autenticação em sites alheios.
- **Limitação de ritmo:** número máximo de análises por utilizador e por período, e por domínio, para evitar abuso e carga indevida sobre o alvo.
- **Segurança da própria aplicação:** palavras-passe com hash, sessões seguras, isolamento de dados entre utilizadores, validação de URLs (incluindo bloqueio de endereços internos para evitar SSRF).
- **Desempenho:** análise concluída em tempo aceitável (objetivo proposto: até 60 s para o conjunto base de verificações), com indicação de progresso.
- **Resiliência:** falha de uma verificação ou da IA não impede a apresentação das restantes.
- **Usabilidade:** interface em português europeu, utilizável em ecrã de computador; mobile é desejável.
- **Rastreabilidade:** cada resultado guarda a evidência, a data e a versão das verificações usadas.
- **Privacidade:** guardar apenas os dados necessários e permitir apagar análises e conta.

### Limites éticos e legais

- As análises destinam-se a websites próprios ou com autorização para teste; o utilizador confirma-o antes de cada pedido.
- Não se explora nenhuma vulnerabilidade, não se fazem ataques de força bruta nem testes de carga.
- Os resultados e as sugestões da IA não constituem certificação de segurança e podem conter erros.
- Qualquer código reutilizado do projeto de referência exige confirmação de licença e identificação da origem.

## 7. Casos de uso principais

Os três casos abaixo correspondem ao entregável 2.2 da WBS (autenticação, análise e consulta de resultados) e serão detalhados com fluxos alternativos na fase de requisitos.

### UC1 — Autenticar-se

- **Ator:** utilizador.
- **Pré-condição:** conta criada ou registo em curso.
- **Fluxo principal:** o utilizador regista-se ou inicia sessão, e é encaminhado para o seu painel.
- **Alternativas:** credenciais inválidas (mensagem genérica); conta já existente; sessão expirada.

### UC2 — Pedir uma análise

1. O utilizador autenticado introduz o URL do website.
2. Confirma que o site é seu ou que tem autorização de teste.
3. O sistema valida o URL e verifica os limites de utilização.
4. O sistema executa as verificações de DNS, HTTPS/TLS, cabeçalhos e cookies e guarda os resultados estruturados.
5. O sistema pede à IA explicações e sugestões para os resultados.
6. O utilizador vê o painel com estado, evidências e recomendações.

**Alternativas:** URL inválido ou bloqueado; limite excedido; site inacessível; falha da IA (os resultados técnicos são apresentados na mesma).

### UC3 — Consultar resultados e histórico

1. O utilizador abre o histórico e escolhe uma análise.
2. O sistema apresenta os resultados com evidências e explicações.
3. O utilizador exporta o relatório (se disponível).

**Regra de permissões:** cada utilizador acede apenas às suas próprias análises.

### UC4 (opcional) — Consultar via assistente de IA

Um assistente autenticado, através do servidor MCP, lista análises e lê resultados do utilizador que lhe concedeu acesso, apenas em modo de leitura.

## 8. Arquitetura, tecnologias e dados (preliminar)

As tecnologias serão decididas pelo grupo na fase 3.1. O projeto de referência usa FastAPI, Next.js e SQLite, que servem como ponto de comparação e não como imposição. Código do projeto de referência só pode ser reutilizado após confirmar a licença e identificar a origem.

### Componentes propostos

| Componente | Responsabilidade | Opções a avaliar |
| --- | --- | --- |
| Interface web | Pedido de análise, painel, histórico, exportação | Next.js ou outra framework web |
| API e autenticação | Contas, sessões, permissões, orquestração das análises | FastAPI ou equivalente |
| Motor de verificações | DNS, HTTPS/TLS, cabeçalhos, cookies; devolve resultados estruturados | Módulos na linguagem do backend |
| Serviço de IA | Gera explicações a partir dos resultados; trata falhas e limites de custo | Fornecedor e modelo a definir em 2.3 |
| Persistência | Utilizadores, análises, resultados, explicações | SQLite para arranque; avaliar alternativa se necessário |
| Gerador de relatórios | Exporta uma análise com evidências e limitações | Formato a decidir (PDF ou Markdown) |
| Servidor MCP (opcional) | Expõe resultados e histórico em modo de leitura | SDK MCP na linguagem do backend |

### Modelo de dados inicial

| Entidade | Campos principais | Relações |
| --- | --- | --- |
| Utilizador | id, email, hash da palavra-passe, data de criação | Tem várias análises |
| Análise | id, URL, data e hora, estado, confirmação de autorização | Pertence a um utilizador; tem vários resultados |
| Resultado | id, tipo de verificação, estado, evidência, valor esperado, severidade | Pertence a uma análise; tem zero ou uma explicação |
| Explicação | id, texto, sugestão, modelo usado, data, estado da validação | Pertence a um resultado |

### Princípio de desenho

A IA fica isolada numa camada própria que consome resultados já gravados. Assim, o sistema funciona sem IA e as explicações podem ser regeneradas ou comparadas entre modelos.

## 9. Sucesso, riscos, planeamento e questões em aberto

### Critérios de sucesso (propostos)

- Todos os requisitos Must (RF01 a RF10) cumprem os seus critérios de aceitação na demonstração final.
- As verificações dão o resultado esperado em todos os websites de teste controlados (WBS 5.1).
- Na avaliação da IA, cada explicação é comparada com a evidência e os erros são registados e analisados (WBS 5.2); o grupo define o limiar aceitável de explicações incorretas.
- A aplicação continua a mostrar resultados técnicos com a IA indisponível (WBS 5.3).
- A documentação permite a um terceiro executar a aplicação e perceber as suas limitações (WBS 6.1).

### Riscos

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| A IA gera explicações incorretas ou inventadas | Utilizador segue conselho errado | Entrada estruturada, ligação a evidências, avaliação em 5.2, aviso visível |
| Custo ou limites do fornecedor de IA | Funcionalidade indisponível ou orçamento excedido | Limite por análise e por utilizador, resposta sem IA, escolha de modelo em 2.3 |
| Uso da ferramenta em sites sem autorização | Problema ético e legal | Confirmação obrigatória, limites de ritmo, apenas verificações passivas, aviso nos termos |
| SSRF ou abuso do pedido de URL | Acesso a recursos internos | Validação de URLs e bloqueio de endereços privados |
| Falsos positivos ou negativos nas verificações | Resultados enganadores | Testes em sites controlados, evidência visível, aviso de que não é certificação |
| Âmbito excessivo para o prazo | Entrega incompleta | Prioridades Must/Should/Could; MCP e comparação como opcionais |
| Reutilização de código sem licença clara | Problema legal | Confirmar licença e origem antes de reutilizar |

### Planeamento

O trabalho segue a WBS inicial. Cada tarefa no GitHub Project ESTG-ESII-WebSecAI identifica código WBS, descrição, critérios de conclusão, responsável e prazo, a acordar pelo grupo.

| Fase | Entregáveis (código WBS) |
| --- | --- |
| 1. Arranque | Definição (1.1); Organização (1.2) |
| 2. Análise | Requisitos (2.1); Casos de uso (2.2); Requisitos da IA (2.3) |
| 3. Desenho | Arquitetura (3.1); Modelo de dados (3.2); Protótipos (3.3) |
| 4. Implementação | Verificações (4.1); Contas e histórico (4.2); Interface (4.3); IA (4.4); Relatórios (4.5) |
| 5. Validação | Testes técnicos (5.1); Avaliação da IA (5.2); Integração (5.3) |
| 6. Fecho | Documentação (6.1); Entrega e demonstração (6.2) |

### Questões em aberto

- [ ] Qual o modelo e fornecedor de IA, e qual o orçamento por análise?
- [ ] Que formato de exportação é obrigatório (PDF, Markdown, outro)?
- [ ] O servidor MCP entra no âmbito da entrega ou fica como extensão?
- [ ] Como se prova a autorização do utilizador para analisar um site: apenas declaração, ou verificação de propriedade do domínio?
- [ ] Que stack tecnológica o grupo escolhe, e há reutilização de código do projeto de referência?
- [ ] Que requisitos de entrega e avaliação define o docente (formato da demonstração, datas)?
- [ ] Quais os limites de ritmo e de utilização por utilizador?
