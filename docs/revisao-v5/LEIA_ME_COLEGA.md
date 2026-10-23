# WebSecAI — entregar esta revisão v5

O pacote WebSecAI_Frontend_2026-10-23_v5.zip inclui **25 ficheiros de código** e dois ficheiros de continuidade alterados/adicionados, um patch cumulativo, manifestos, instruções e capturas sem dados pessoais de conta.

É uma entrega de alterações sobre a devolução WebSecAI_devolucao_alteracoes.zip (SHA-256 f5070bb54b4b919cbfff8149e18b769bc3d025b7eaec1bec00d4e3d5a19bda71). A base completa foi WebSecAI_Continuacao_2026-10-22_v2.zip. Não é uma pasta de instalação completa.

**Inclui as correções v4 de registo/sessão e a nova experiência visual v5.** Aplicar a partir da devolução do colega; não aplicar automaticamente por cima de uma v4 já integrada. Comparar hashes e diferenças se existirem alterações posteriores.

Ler FRONTEND_V5.md para funcionalidades, limitações, testes e ordem de publicação. REVISAO.md preserva os resultados da revisão de acesso anterior; não representa uma nova aceitação online da v5.

1. Criar um ramo/guardar o estado atual. Executar git apply --check frontend_2026-10-23.patch na raiz que contém codigo/. Resolver conflitos conscientemente.
2. Aplicar/rever o patch ou integrar os ficheiros alterados por comparação. O manifesto contém hashes antes/depois. A prova isolada de aplicação e de igualdade de ficheiros está no manifesto; não implica compatibilidade com alterações ainda não recebidas.
3. Repetir os dois testes JS a partir de codigo/ e a build de frontend, usando a API correta da instalação. Não foram alteradas dependências ou locks.
4. Publicar primeiro as correções v4 do backend se ainda não estiverem online. Manter public_registration_enabled=false em produção, autorização por dono, quotas, CORS e contas internas.
5. Publicar a interface pelo processo Cloudflare existente, construída com NEXT_PUBLIC_API_BASE_URL da API pública. Não copiar .next de localhost. Validar login das três contas, demonstração, fontes, filtros, cronologia, mapa, referências e PDF; medir CPU no Free.

O Gonçalo pode testar localmente em http://127.0.0.1:3001, API 8001, usando a sua conta local. Contas, histórico, base e configurações privadas não acompanham o ZIP. O mapa não cria associações de incidentes: representa apenas a recolha das evidências.

Antes de considerar a instalação online aceite, o responsável deve confirmar privadamente a rotação da credencial Neon mencionada na entrega anterior e criar as contas internas. Não enviar segredos no chat.

Não houve push, merge, deploy, custos ou novas chamadas a fornecedores nesta revisão. A publicação remota não foi feita. A ideia de password própria continua adiada.
