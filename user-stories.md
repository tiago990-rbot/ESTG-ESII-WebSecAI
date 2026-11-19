# User stories — WebSecAI

**Projeto:** Engenharia de Software II  
**Equipa:** Pedro Mano, Tiago Melo e Gonçalo Cordeiro

As histórias descrevem o valor esperado para o utilizador. Os critérios abaixo são verificáveis e podem ser usados em cartões do Kanban. Um critério descrito não significa que o teste já tenha passado. Os identificadores UC remetem para os [casos de uso](casos-de-uso.md).

### US-01 — Ativar conta por convite

Como pessoa convidada, quero ativar a minha conta através de um convite, para escolher a minha palavra-passe em privado.

- **Critério de aceitação:** Um convite válido permite ativar a conta; um convite expirado ou já utilizado é recusado.
- **Casos de uso:** UC-01.

### US-02 — Iniciar e terminar sessão

Como utilizador autorizado, quero iniciar e terminar sessão, para proteger o acesso ao meu histórico.

- **Critério de aceitação:** Credenciais válidas permitem entrar; credenciais inválidas não criam sessão; após sair, a área privada pede novo login.
- **Casos de uso:** UC-02.

### US-03 — Alterar palavra-passe

Como utilizador autenticado, quero alterar a minha palavra-passe, para manter o controlo sobre a minha conta.

- **Critério de aceitação:** A alteração exige a palavra-passe atual; após sucesso, a anterior e as sessões antigas deixam de ser válidas.
- **Casos de uso:** UC-03.

### US-04 — Repor palavra-passe

Como utilizador autorizado, quero repor a minha palavra-passe através de um link privado, para recuperar o acesso sem partilhar credenciais.

- **Critério de aceitação:** Um link válido permite definir uma nova palavra-passe uma vez; um link expirado ou reutilizado é recusado.
- **Casos de uso:** UC-04.

### US-05 — Executar análise técnica autorizada

Como utilizador autenticado, quero analisar um website que estou autorizado a testar, para identificar configurações que merecem revisão.

- **Critério de aceitação:** O fluxo exige confirmação de autorização; apresenta os resultados técnicos obtidos e sinaliza verificações incompletas.
- **Casos de uso:** UC-05.

### US-06 — Investigar um domínio ou uma mensagem

Como utilizador autenticado, quero investigar um domínio, link ou mensagem suspeita, para reunir referências num único dossiê.

- **Critério de aceitação:** O pedido válido cria um dossiê; o modo público não executa verificações técnicas; as fontes opcionais só são consultadas quando selecionadas.
- **Casos de uso:** UC-06.

### US-07 — Investigar um domínio ou uma mensagem (estado das fontes)

Como utilizador autenticado, quero ver o estado de cada fonte, para distinguir ausência de correspondências de falhas.

- **Critério de aceitação:** Uma consulta sem correspondências é distinguida de uma fonte não solicitada, indisponível ou com erro.
- **Casos de uso:** UC-06, UC-07.

### US-08 — Consultar dossiês e explorar evidências

Como utilizador autenticado, quero filtrar referências e explorar a cronologia e o mapa, para perceber quando e de onde vieram as evidências.

- **Critério de aceitação:** Os filtros restringem as vistas aplicáveis; datas desconhecidas não são inventadas; o mapa identifica a origem da recolha.
- **Casos de uso:** UC-07.

### US-09 — Consultar dossiês e explorar evidências (privacidade)

Como utilizador autenticado, quero manter os meus dossiês privados, para impedir que outra conta consulte ou altere o meu trabalho.

- **Critério de aceitação:** Com duas contas de teste, a segunda não consegue consultar, exportar ou remover o dossiê da primeira, mesmo conhecendo o endereço.
- **Casos de uso:** UC-07, UC-12, UC-14.

### US-10 — Rever uma evidência

Como proprietário do dossiê, quero registar uma avaliação e notas sobre uma evidência, para preservar a minha revisão para consulta posterior.

- **Critério de aceitação:** A avaliação fica no histórico; uma revisão posterior não apaga a anterior; guardar uma revisão não inicia nova chamada à IA.
- **Casos de uso:** UC-08.

### US-11 — Consultar síntese e fazer perguntas à IA

Como proprietário do dossiê, quero ler uma síntese e colocar perguntas sobre as evidências, para interpretar os resultados com referências verificáveis.

- **Critério de aceitação:** As referências apontam para evidências do dossiê; se a síntese falhar, o erro é indicado e as evidências ficam disponíveis.
- **Casos de uso:** UC-09.

### US-12 — Repetir a recolha de um módulo

Como proprietário do dossiê, quero repetir apenas um módulo que ficou incompleto, para obter o resultado em falta sem repetir a investigação.

- **Critério de aceitação:** A tentativa é limitada ao módulo escolhido; os restantes resultados mantêm-se e as quotas continuam a aplicar-se.
- **Casos de uso:** UC-10.

### US-13 — Comparar recolhas

Como utilizador autenticado, quero comparar recolhas compatíveis, para identificar alterações sem confundir contextos.

- **Critério de aceitação:** Quando existem recolhas compatíveis, são apresentadas as diferenças; na ausência delas, o sistema explica que não há base de comparação.
- **Casos de uso:** UC-11.

### US-14 — Exportar relatório PDF

Como proprietário da análise ou do dossiê, quero descarregar um relatório PDF, para guardar um resumo com as evidências e limitações.

- **Critério de aceitação:** O PDF é gerado a partir do resultado guardado, sem nova consulta aos fornecedores; o acesso respeita a propriedade dos dados.
- **Casos de uso:** UC-12.

### US-15 — Explorar a demonstração

Como utilizador autenticado, quero explorar uma demonstração com dados fictícios, para aprender o fluxo sem consumir quotas.

- **Critério de aceitação:** O dossiê identifica os dados como fictícios e não efetua pedidos ao alvo, a fontes externas ou à IA.
- **Casos de uso:** UC-13.

### US-16 — Remover um dossiê próprio

Como proprietário do dossiê, quero remover uma investigação que já não preciso, para gerir o meu histórico.

- **Critério de aceitação:** O dossiê próprio é removido após confirmação; cancelar mantém o registo e outra conta não o pode remover.
- **Casos de uso:** UC-14.

## Propostas futuras

| ID | História | Condição para aceitação |
| --- | --- | --- |
| US-F01 | Como membro do grupo, quero colaborar num dossiê partilhado, para rever evidências em equipa. | Acesso concedido explicitamente, com permissões próprias e sem exposição dos dossiês pessoais. |
| US-F02 | Como estudante, quero executar casos de teste num laboratório do grupo, para demonstrar como se confirma uma falha. | Execução restrita a um ambiente autorizado, com limites e evidência observada. |
| US-F03 | Como utilizador, quero consultar resultados através de um assistente compatível com MCP, para explorar os meus dados autorizados. | O assistente só consulta os dados permitidos à conta, dentro do âmbito aprovado. |

Estas propostas não estão implementadas nem fazem parte dos critérios de aceitação da versão atual.
