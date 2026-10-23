# WebSecAI v7 - cronologia e mapa no relatório

Revisão local pedida pelo Gonçalo após a v6: incluir gráficos no próprio PDF antes de enviar ao colega. Esta versão preserva a análise profissional da v6 e acrescenta visualizações vetoriais construídas a partir dos dados guardados. Sem novas dependências, consultas ou consumo de IA na exportação. Sem alterações de frontend, schema ou migrações.

## O que passa a aparecer

- Secção 06: cronologia com três eixos independentes - publicação, incidente e consulta. Mais recentes no topo, espaçamento uniforme, sem escala de duração. Datas desconhecidas ou inválidas não são substituídas por outra data. Valores com hora são normalizados para UTC; datas de calendário mantêm a precisão original.
- A cronologia agrupa referências da mesma data, mostra o número de referências e liga E# ao anexo. Até cinco datas por coluna e seis citações por data, com aviso explícito; as restantes continuam integralmente no anexo. O tamanho adapta-se ao número de datas.
- Quando a cronologia é curta, inclui barras de volume por módulo. Estas contam referências, nunca incidentes, risco ou confirmação independente. Os cinco módulos com mais resultados são apresentados individualmente; os restantes aparecem em Outros módulos.
- Secção 07: mapa de proveniência, dossiê -> módulo consultado -> evidência. Linhas a tracejado/âmbar distinguem alertas gerais, candidatos por produto, homónimos, alegações, conteúdo por verificar e resultados anteriores conservados. A cor não é gravidade. O mapa não cria ligações causais ou confirma intrusão.
- Até 24 evidências selecionadas por alternância de módulos; paginação em blocos de 12, contagens e omissões explícitas. Títulos longos abreviados apenas no mapa. E# abre o conteúdo integral no anexo. Evidências da lista anterior permanecem no anexo e não são acrescentadas como atuais. Correlações interpretativas continuam na secção 01 com as respetivas ressalvas.
- O anexo passa a secção 08. A numeração E# conserva a correspondência com a interface e as referências da IA.

## Implementação e provas

O gerador continua em codigo/backend/app/services/investigation_pdf.py. O novo investigation_pdf_visuals.py contém as vistas vetoriais e modelos de leitura puros. Não captura o ecrã do site, não usa um serviço externo de gráficos e não precisa do navegador para exportar. Gráficos legíveis em zoom/impressão, com o mesmo olho e cores do relatório.

Validação final desta revisão: 27 testes de inteligência/gráficos aprovados, mais cinco cenários PDF existentes aprovados (32 no total). Cobrem precisão/datas desconhecidas, zonas horárias, associação incerta, seleção equilibrada, ausência de recolha na exportação, isolamento e geração com 50 referências/títulos extensos ou sem evidências atuais. Apenas o aviso Starlette/httpx já existente. A suite completa e build da v6 não foram repetidas: não houve alteração de frontend ou dependências.

Exemplo de nove páginas renderizado e revisto na íntegra; 31 ligações (29 internas para destinos válidos e duas externas), sem texto fora da margem segura ou glifos de substituição. Cenário adicional de 50 referências usado para rever visualmente a cronologia e os dois mapas paginados. O exemplo é totalmente fictício, escrito por regras e sem chamada a um modelo. Não mede qualidade de IA real.

O exemplo v7 em output/pdf/ é produzido pelo mesmo gerador do endpoint. Reprodução local: scripts/gerar_relatorio_exemplo_v7.py na workspace do Gonçalo; noutro computador usar evaluations/report_fixture.py + investigation_pdf. O script local de conveniência não é necessário ao funcionamento da aplicação.

## Entrega e aceitação

Usar apenas o novo pacote cumulativo v7 sobre a devolução original. Inclui as alterações anteriores v4/v5/v6, esta revisão, instruções, exemplo e imagens de demonstração. Não aplicar v6 e depois o patch cumulativo v7 sem comparar. Se a v6 já tiver sido integrada, rever o diff entre as versões; não sobrescrever alterações do colega.

Atualizar o backend e validar a exportação autenticada antes de aceitar online. A interface continua com o botão PDF completo. Exportar não muda o estado nem atualiza a síntese; se estiver desatualizada, o aviso/arquivo conservam-se. O alojamento gratuito continua sujeito à aceitação real de runtime/CPU, contas e PostgreSQL; não houve deploy, push, alterações de credenciais ou custos nesta revisão.
