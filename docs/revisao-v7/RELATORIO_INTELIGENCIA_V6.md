# WebSecAI — análise de inteligência e relatório integrado v6

Pedido autorizado em 23/10/2026: transformar os resultados em informação pertinente, produzir um relatório profissional com identidade WebSecAI, perguntas respondidas, conclusões e correlações fundamentadas, e juntar análise técnica e Threat Intelligence num dossiê. Implementado na cópia local candidato/, sem publicação.

## Como funciona e porquê

1. **Recolher no mesmo dossiê.** O formulário distingue Investigação pública de Dossiê completo. O modo completo junta a pesquisa e as verificações técnicas já existentes; exige confirmação explícita de website próprio/autorizado. A demonstração ignora qualquer alvo introduzido e usa um domínio reservado, sem rede. Uma ligação no histórico do painel técnico permite preparar um dossiê para o mesmo domínio; não o inicia automaticamente nem reutiliza silenciosamente medições antigas.
2. **Preparar o contexto.** As medições técnicas passam a incluir uma evidência de postura com score/resumo, além dos findings. Não são enviados cookies, valores de headers ou detalhes brutos à IA. Até 24 evidências são selecionadas por alternância de módulos, com prioridade aos findings técnicos mais relevantes. Assim, 15 findings não excluem as notícias. A IA recebe datas separadas, proveniência, estado dos módulos e o número de evidências omitidas.
3. **Analisar com um contrato verificável.** O prompt analyst-v4-intelligence pede resumo executivo, conclusões, correlações, seis respostas, prioridades e lacunas. As conclusões distinguem observação, inferência e hipótese. Cada ação tem motivo e critério de conclusão. A confiança é qualitativa; não é uma probabilidade. O modelo não recebe ferramentas nem autorização para executar ações.
4. **Validar antes de guardar.** Pydantic valida tipos, tamanhos e os identificadores citados. O sistema exige as seis perguntas distintas, rejeita referências inexistentes/repetidas, respostas afirmativas sem referências e confiança elevada apoiada em homónimos, alegações, referências por verificar, KEV geral/candidato ou resultados conservados. Correlações precisam de pelo menos duas evidências; a mesma origem ou módulo não justifica confiança elevada. Isto não é uma verificação semântica integral: uma citação existente não garante que todas as palavras da conclusão estejam corretas.
5. **Apresentar e exportar.** O site mostra conclusões, relações possíveis/divergências, perguntas expansíveis, prioridades e lacunas. As citações abrem a evidência. O PDF é construído a partir dos dados guardados e não chama fornecedores/IA novamente. A exportação é consistente com a investigação; não cria uma conclusão diferente a cada download nem aumenta consumo por descarregar.

## As seis perguntas

- Há referências a incidentes anteriores?
- As referências dizem respeito à mesma organização?
- Existem sinais atuais de ameaça?
- Que fragilidades técnicas foram observadas?
- O histórico e a configuração atual estão relacionados?
- O que deve ser feito primeiro?

Informação insuficiente é uma resposta válida. Coexistência de uma falha técnica e de uma notícia histórica não prova causalidade. Um alerta de exploração conhecida não prova versão afetada, comprometimento atual ou exploração no alvo. A IA pode formular uma hipótese útil desde que a identifique e indique o que permitiria confirmá-la.

## PDF profissional

Documento com olho vetorial/logótipo WebSecAI, identidade branca/azul/turquesa para leitura e impressão, cabeçalhos, paginação e seis secções após o resumo executivo: conclusões/correlações, perguntas, prioridades, contexto técnico, cobertura/método e anexo integral de evidências. As referências [E#] são clicáveis para o anexo, que preserva origem e datas. Horas são apresentadas em UTC, explicitamente; datas de calendário não recebem uma hora inventada.

Não é mostrada uma síntese desatualizada como conclusão atual: é conservada em arquivo com aviso. Resultados técnicos conservados após uma tentativa falhada também recebem aviso. Na ausência de IA, o PDF declara a falta de análise atual e organiza os factos disponíveis. Não mascara regras locais como texto de um modelo.

O exemplo WebSecAI_Relatorio_Inteligencia_Exemplo_v6.pdf tem **sete páginas**, todas renderizadas e revistas; 17 anotações de ligação e marca DEMONSTRAÇÃO em todas as páginas. Foi escrito por regras, sem avaliação de empresa real ou modelo. O gerador é o mesmo do endpoint da aplicação, não uma maquete independente. A geração do exemplo é reproduzível com scripts/gerar_relatorio_exemplo_v6.py na workspace do Gonçalo ou evaluations/report_fixture.py + investigation_pdf na cópia do backend.

## Compatibilidade, custos e limites

- Sem migração ou tabela nova: análise estruturada no JSON de relatórios existente. Relatórios antigos continuam legíveis. O fingerprint inclui a versão do prompt; resumos anteriores podem ficar desatualizados e precisar de atualização explícita.
- Quotas e reserva por pedido mantidas. Uma geração reserva uma chamada; mantém-se uma única recuperação de formato, também reservada. Não se repetem pesquisas/fontes para escrever o relatório. O máximo de saída passou de 1800 para 4600 tokens e a seleção de entrada é limitada; o consumo real e limites por minuto dependem do modelo/plano. Os limites não são aumentados automaticamente.
- A configuração local usada nesta revisão mantém pesquisa/IA a zero e sem chaves externas. Não foram copiadas chaves da instalação antiga. Não houve novas chamadas reais a modelos/fornecedores, custos, push, merge, deploy ou acesso a segredos.
- A documentação oficial [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) foi consultada em 23/10/2026. O schema enviado fecha objetos e exige todas as propriedades; o modo strict é selecionado para os modelos listados no código como suportados, incluindo o Qwen configurado. O fallback continua sujeito à validação local. Documentação e respostas controladas não substituem uma chamada real de aceitação.
- Password própria continua adiada. Não houve atualização dos dois PDFs antigos de planeamento: este é o novo relatório produzido pela aplicação.

## Verificação

Os testes acrescentados cobrem contrato completo/compatibilidade, perguntas distintas, referências, confiança indevida, origem repetida, seleção equilibrada, minimização dos dados técnicos, pipeline completo só com autorização, demonstração sem rede/IA, exportação sem repetir recolha, isolamento de conta, HTML não confiável e resultados técnicos conservados. A suite de backend e build final estão registadas no estado/manifesto da revisão. PostgreSQL continua omitido por falta de ambiente local dedicado; não apontar testes destrutivos ao Neon.

A revisão inclui aceitação de interface com demonstração: sete evidências (três técnicas), duas conclusões, uma correlação contextual, seis respostas e duas prioridades. Não é uma avaliação de qualidade de um LLM. A aceitação com fontes e modelo reais continua pendente de configuração privada e de uma consulta limitada/consentida.

## Integrar e aceitar online

O pacote v6 é **cumulativo**, relativamente à devolução original do colega: inclui correções v4, frontend v5 e relatório/IA v6. Não aplicar sucessivamente os patches cumulativos v4/v5/v6. Se houver mudanças posteriores, comparar hashes/diffs e integrar num ramo. O pacote não é uma instalação completa e não contém contas, bases, ambientes, dependências ou build local.

Publicar primeiro o backend atualizado e depois o frontend construído com a API pública. Preservar registo interno, autorização por dono, quotas e CORS. Confirmar privadamente a rotação da credencial Neon já assinalada. Com contas internas e acesso gratuito confirmado, validar um domínio autorizado em Dossiê completo, conferir cada conclusão e a sua origem, fazer uma pergunta e descarregar o PDF. Comparar com um caso sem resultados, uma alegação e um homónimo. Medir consumo/CPU do alojamento; a build local não prova aceitação em Cloudflare Free.

Próxima aceitação real deve registar: domínio/âmbito autorizado, momento, módulos e cobertura, modelo/prompt, pedidos/tokens/limites disponíveis, referências usadas/omitidas, divergências e revisão humana das conclusões. Não reportar precisão geral a partir de um só exemplo.
