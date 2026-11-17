# Casos de uso — WebSecAI

**Projeto:** Engenharia de Software II  
**Equipa:** Pedro Mano, Tiago Melo e Gonçalo Cordeiro

Este documento descreve os fluxos da versão integrada do WebSecAI. As verificações técnicas destinam-se a websites próprios ou autorizados. Uma referência recolhida não comprova uma intrusão. MCP, espaço de trabalho partilhado e laboratório de testes ativos são propostas futuras e estão fora destes fluxos.

## Atores

| Ator | Papel |
| --- | --- |
| Pessoa convidada | Ativa uma conta autorizada por link privado. |
| Utilizador autenticado | Executa análises, investiga, revê evidências e consulta o seu histórico. |
| Responsável pela instalação | Autoriza contas e emite links privados através do utilitário de gestão. |
| Fornecedores externos | Devolvem dados públicos ou sínteses, conforme a disponibilidade e as quotas. |

## Fluxos

### UC-01 — Ativar conta por convite

- **Atores:** Pessoa convidada; responsável pela instalação.
- **Pré-condições:** O email está autorizado e existe um convite válido.
- **Fluxo principal:** O responsável envia o link privado. A pessoa abre-o, define e confirma a palavra-passe. O sistema ativa a conta e consome o convite.
- **Alternativas e erros:** Um convite expirado, substituído ou já utilizado é recusado. A pessoa pede um novo convite ao responsável.
- **Resultado esperado:** A conta pode iniciar sessão.

### UC-02 — Iniciar e terminar sessão

- **Atores:** Utilizador autorizado.
- **Pré-condições:** A conta está ativa.
- **Fluxo principal:** O utilizador introduz as credenciais. O sistema valida-as e abre a área autenticada. Ao escolher Sair, o utilizador volta à área pública.
- **Alternativas e erros:** Se as credenciais forem inválidas ou o acesso estiver vedado, a sessão não é iniciada.
- **Resultado esperado:** O acesso à área privada depende de uma sessão válida.

### UC-03 — Alterar palavra-passe

- **Atores:** Utilizador autenticado.
- **Pré-condições:** O utilizador conhece a palavra-passe atual.
- **Fluxo principal:** No perfil, introduz a palavra-passe atual, a nova e a confirmação. O sistema valida e guarda a alteração.
- **Alternativas e erros:** Se a palavra-passe atual estiver incorreta ou a nova não cumprir os requisitos, nada é alterado.
- **Resultado esperado:** A nova palavra-passe fica ativa e as sessões anteriores deixam de ser válidas.

### UC-04 — Repor palavra-passe

- **Atores:** Utilizador autorizado; responsável pela instalação.
- **Pré-condições:** Existe um link de reposição válido, emitido pelo responsável.
- **Fluxo principal:** O utilizador abre o link privado, escolhe a nova palavra-passe e confirma-a. O sistema consome o link e permite novo login.
- **Alternativas e erros:** Se o link estiver expirado ou usado, é necessário pedir outro. Não há envio automático de email.
- **Resultado esperado:** A conta e os dossiês mantêm-se; as sessões anteriores são invalidadas.

### UC-05 — Executar análise técnica autorizada

- **Atores:** Utilizador autenticado.
- **Pré-condições:** O utilizador é proprietário do alvo ou tem autorização para o testar.
- **Fluxo principal:** Indica o domínio ou URL e confirma a autorização. O sistema executa as verificações aplicáveis e apresenta resultados, por exemplo sobre DNS, TLS ou cabeçalhos HTTP.
- **Alternativas e erros:** Se o alvo for inválido ou não autorizado, a análise não deve avançar. Uma falha de verificação é apresentada como limitação.
- **Resultado esperado:** O resultado fica no histórico técnico do utilizador.

### UC-06 — Investigar um domínio ou uma mensagem

- **Atores:** Utilizador autenticado.
- **Pré-condições:** O utilizador tem uma sessão válida e fornece um domínio, URL ou mensagem para analisar.
- **Fluxo principal:** Escolhe o tipo de investigação e as fontes opcionais necessárias. Submete o pedido. O sistema recolhe os dados disponíveis e atualiza o dossiê com resultados e estados por fonte.
- **Alternativas e erros:** Se uma fonte falhar ou exceder a quota, o dossiê pode ficar parcial. A investigação pública não faz verificações técnicas ao alvo.
- **Resultado esperado:** O dossiê e as evidências disponíveis ficam no histórico individual.

### UC-07 — Consultar dossiês e explorar evidências

- **Atores:** Utilizador autenticado.
- **Pré-condições:** Existe pelo menos um dossiê próprio.
- **Fluxo principal:** Abre o histórico, seleciona um dossiê e consulta o panorama, as fontes, a cronologia ou o mapa. Usa os filtros para localizar referências.
- **Alternativas e erros:** Sem resultados, o sistema apresenta um estado vazio. Um endereço direto não dá acesso a um dossiê de outra conta.
- **Resultado esperado:** O utilizador consegue identificar a origem e os limites das evidências.

### UC-08 — Rever uma evidência

- **Atores:** Proprietário do dossiê.
- **Pré-condições:** A evidência pertence a um dossiê próprio.
- **Fluxo principal:** Seleciona a evidência, atribui uma avaliação e acrescenta uma nota, se necessário. O sistema regista a revisão no histórico.
- **Alternativas e erros:** Se a evidência mudar, a revisão anterior pode ficar desatualizada. A revisão humana não lança uma nova síntese automaticamente.
- **Resultado esperado:** A avaliação fica registada sem apagar as revisões anteriores.

### UC-09 — Consultar síntese e fazer perguntas à IA

- **Atores:** Proprietário do dossiê.
- **Pré-condições:** O dossiê tem dados para interpretar. A integração de IA está disponível dentro das quotas.
- **Fluxo principal:** Consulta a síntese ou coloca uma pergunta sobre o dossiê. Quando a resposta é válida, o sistema apresenta-a com referências às evidências.
- **Alternativas e erros:** Se faltar acesso, quota ou uma resposta válida, o sistema indica a limitação e mantém as evidências.
- **Resultado esperado:** O utilizador pode rever as conclusões e conferir as referências.

### UC-10 — Repetir a recolha de um módulo

- **Atores:** Proprietário do dossiê.
- **Pré-condições:** O módulo está elegível para nova tentativa e existem recursos disponíveis.
- **Fluxo principal:** Na vista Fontes, escolhe o módulo e pede nova recolha. O sistema atualiza o estado desse módulo e mantém os restantes resultados.
- **Alternativas e erros:** Se a fonte estiver indisponível ou sem quota, o sistema apresenta a limitação sem iniciar novo lote.
- **Resultado esperado:** O dossiê conserva os resultados dos outros módulos.

### UC-11 — Comparar recolhas

- **Atores:** Utilizador autenticado.
- **Pré-condições:** Existem recolhas próprias compatíveis para comparar.
- **Fluxo principal:** Abre a comparação e consulta o que mudou entre a recolha atual e a anterior, com base nos dados disponíveis.
- **Alternativas e erros:** Se não existir uma recolha comparável, o sistema indica essa limitação. Alertas gerais não são apresentados como alterações específicas do alvo.
- **Resultado esperado:** As diferenças podem ser revistas no contexto das fontes.

### UC-12 — Exportar relatório PDF

- **Atores:** Proprietário da análise ou do dossiê.
- **Pré-condições:** Existe um resultado próprio disponível.
- **Fluxo principal:** Escolhe a opção de exportação. O sistema gera o PDF correspondente aos dados guardados e disponibiliza a descarga.
- **Alternativas e erros:** Em caso de erro, o sistema não deve apresentar a exportação como concluída. Outro utilizador não pode descarregar o PDF por endereço direto.
- **Resultado esperado:** O relatório pode ser guardado sem repetir a recolha.

### UC-13 — Explorar a demonstração

- **Atores:** Utilizador autenticado.
- **Pré-condições:** O utilizador pode aceder à área de investigação.
- **Fluxo principal:** Seleciona Explorar demonstração. O sistema cria um dossiê fictício e identifica os dados como demonstrativos.
- **Alternativas e erros:** A demonstração não consulta fontes externas, não contacta o alvo e não chama a IA.
- **Resultado esperado:** O utilizador pode explorar o fluxo sem consumir quotas externas.

### UC-14 — Remover um dossiê próprio

- **Atores:** Proprietário do dossiê.
- **Pré-condições:** O dossiê é do utilizador e está disponível para remoção.
- **Fluxo principal:** Seleciona Remover e confirma a operação. O sistema verifica a autorização e remove o dossiê.
- **Alternativas e erros:** Se a operação for cancelada ou o dossiê pertencer a outra conta, não é removido.
- **Resultado esperado:** O dossiê deixa de aparecer no histórico.

## Estado da validação

Na validação registada em 24/10/2026, URLhaus e Tavily responderam numa investigação pública. A síntese IA não produziu uma resposta válida; as evidências foram preservadas. A geração de PDF foi testada localmente, mas a descarga online não ficou confirmada nessa validação. A descrição dos fluxos não substitui os respetivos testes de aceitação.

Ver também [User stories e critérios de aceitação](user-stories.md).
