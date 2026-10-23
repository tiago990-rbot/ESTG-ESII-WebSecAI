# WebSecAI — revisão visual v5, 23/10/2026

O pedido foi tornar o site mais distinto, dinâmico e orientado à investigação, preservando Threat Intelligence e as funcionalidades existentes. Esta entrega é local; não foi publicada.

## Identidade e experiência

- Símbolo de olho com marcas de radar, desenhado em SVG; substitui o quadrado e acompanha um novo ícone do separador.
- Azul profundo, turquesa e âmbar para incerteza. Tipografia de sistema e uma lente ilustrativa com movimento discreto, sem fontes externas, imagens remotas, bibliotecas novas ou serviços pagos.
- Página inicial e área de investigação redesenhadas; formulário com contexto opcional, percurso de três etapas e arquivo pesquisável por alvo e estado.
- Dossiê com seis vistas: Panorama, Evidências, Cronologia, Mapa de relações, Assistente IA e Fontes. A barra de vistas acompanha a leitura. O painel técnico mantém o seu fluxo e ganha uma ligação clara à investigação de ameaças.

## Exploração com limites explícitos

Os filtros de pesquisa, módulo e contexto acompanham as vistas Evidências/Cronologia/Mapa. As referências E# mantêm a numeração original. Ao seguir uma citação ou selecionar Examinar no mapa, o sistema limpa os filtros e abre, destaca e foca a evidência. Ligações diretas #evidence-ID sobrevivem ao recarregamento.

A cronologia permite escolher publicação, incidente ou consulta. Datas desconhecidas/inválidas ficam separadas. Não preenche datas de incidente com datas de publicação, entrada KEV ou consulta.

O grafo mostra **proveniência de recolha: dossiê → módulo → evidência**. Cada ligação corresponde a um resultado existente. Não identifica atacantes nem representa intrusões, organizações relacionadas ou um mesmo incidente sem prova. A cor distingue contexto/necessidade de revisão, sem criar um score de risco. Os alertas KEV gerais e candidatos por produto mantêm as suas limitações. O painel permite abrir a evidência completa e a ligação original validada.

O mapa carrega no navegador quando a vista é aberta. Mostra até 24 evidências dos filtros atuais, com aviso do restante; a lista completa mantém-se na vista Evidências. Em ecrãs pequenos tem deslocação horizontal própria e uma lista alternativa acessível. Não há simulação de dados ao vivo: a animação da lente é ilustrativa e a demonstração é identificada como fictícia.

Mantidos: fontes e repetição por módulo, exigência de autorização técnica, sínteses antigas, perguntas elegíveis, arquivo de evidências anteriores, grupos candidatos conservadores, comparação, mensagens, exportação integral e confirmação de remoção. Os filtros não alteram o PDF nem a base de dados.

## Verificação local

- Build Next.js 15.5.28 com verificação de tipos e geração de páginas aprovado; base pública da API usada na build local: http://127.0.0.1:8001.
- node tests/evidence-view.mjs: testes do módulo real em VM, cobrindo homónimos, KEV, datas inválidas/desconhecidas, filtros com acentos, limites do grafo, identidade das ligações e ausência de mutação dos dados/numeração. Zero pedidos externos.
- node tests/auth-client.mjs: regressão das correções de sessão/política de registo aprovada, com respostas controladas e zero pedidos externos.
- Navegador: mudança domínio/mensagem, contexto opcional e campo de autorização técnica; pesquisa do arquivo e vazio; filtros partilhados; cronologia com data de incidente desconhecida e publicação conhecida; seleção do grafo com Enter; mapa → evidência; IA → E1; recarregamento por ligação direta; Fontes e navegação por End; todos os aria-controls dos separadores têm painel; exportação PDF concluída.
- Ecrã pequeno: viewport 390×844, área útil 375 px com barra; largura da página igual à área útil, sem overflow global no formulário/mapa/evidências. O mapa desloca apenas no seu contentor. Tamanho temporário reposto após o teste.
- Fluxo técnico anterior abriu corretamente, sem iniciar novos scans. Capturas novas estão em evidencias/frontend-*.png.

Não foi repetida a suite completa de backend nesta fase exclusivamente visual. As execuções SQLite anteriores estão em REVISAO.md (112 aprovados/1 PostgreSQL omitido, depois 16 aprovados/1 omitido). Não houve teste novo de PostgreSQL, modelo real, autenticação de fornecedores ou medição de CPU Cloudflare. O build local não prova aceitação em Workers Free.

## Integração pelo colega

Esta entrega **é cumulativa**: inclui as correções de acesso/sessão da v4 e a revisão visual v5, relativamente ao ZIP devolvido pelo colega. Não é necessário aplicar primeiro o patch v4. Se a v4 ou outras alterações já tiverem sido integradas, comparar os ficheiros/hashes e resolver conscientemente; não forçar um patch sobre outro nem substituir a pasta inteira.

1. Guardar o estado atual num ramo, comparar MANIFEST_ALTERACOES_REVISAO.json e executar git apply --check frontend_2026-10-23.patch na raiz que contém codigo/.
2. Rever e aplicar o patch. A verificação isolada usa git -c core.autocrlf=false -c core.eol=lf apply; não alterar a configuração global de finais de linha. Também seguem os ficheiros alterados para integração por comparação.
3. A partir de codigo/: node tests/auth-client.mjs e node tests/evidence-view.mjs. A partir de codigo/frontend/: npm ci e npm run build. Não foram alteradas dependências/locks nesta revisão.
4. Se as correções v4 do backend ainda não estiverem online, publicar primeiro esse backend. GET /api/v1/auth/configuration deve devolver public_registration_enabled=false na instalação de produção do grupo.
5. Construir o frontend com NEXT_PUBLIC_API_BASE_URL a apontar à API pública correta. Não publicar a pasta .next construída para localhost. Usar o processo Cloudflare já existente e manter CORS restrito à origem pretendida.
6. Aceitar login das três contas internas, demonstração, filtros, cronologia, mapa, citações, histórico e PDF no endereço publicado. Confirmar isolamento entre contas e medir CPU/limites do plano gratuito. O comportamento do Worker deve ser validado pelo responsável.

Continuam pendentes a confirmação privada da rotação da credencial Neon mencionada na entrega anterior, criação das contas internas e aceitação da instalação online. Nunca enviar credenciais no chat. A nova conta e os dados do localhost não acompanham o pacote.

Sem .env, bases, passwords, tokens, cookies, node_modules, .venv, .next ou dados de conta. Sem push, merge, deploy, custos ou consultas novas a fornecedores. Password própria permanece como ideia para uma fase posterior. Os dois PDFs de projeto anteriores estão preservados; este documento complementa-os, sem alegar que foram atualizados nesta revisão.
