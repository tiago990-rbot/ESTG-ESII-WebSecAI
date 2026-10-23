# Entrega WebSecAI v7 - inteligência com relatório visual

Esta é a revisão atual para integrar. Inclui cumulativamente acesso v4, frontend v5, inteligência v6 e gráficos PDF v7, sobre WebSecAI_devolucao_alteracoes.zip. É um pacote de alterações, não uma instalação completa. Preservar as mudanças posteriores do colega; comparar antes de aplicar. Não aplicar patches cumulativos v4/v5/v6/v7 em sequência.

1. Ler PDF_VISUAL_V7.md e RELATORIO_INTELIGENCIA_V6.md. Guardar o trabalho atual num ramo. Conferir MANIFEST_ALTERACOES_REVISAO.json e executar git apply --check inteligencia_2026-10-23_v7.patch na raiz que contém codigo/. Se houver conflitos, integrar por comparação; não substituir pastas inteiras. O patch foi aplicado numa cópia isolada e os hashes finais conferidos na origem.
2. No backend, manter os locks existentes. Executar python -m pytest -q --tb=short apenas com base de testes local dedicada; nunca Neon. Não há nova dependência, migração ou alteração do schema nesta revisão.
3. Os testes diretamente afetados da origem passaram (32). A build frontend da v6 foi preservada; nesta revisão só mudou o backend PDF e a documentação. No ambiente de destino continuar a executar os checks usuais e build com a API pública.
4. Publicar primeiro o backend atualizado; integrar/publicar a interface cumulativa se as alterações anteriores ainda não estiverem online. Não copiar .env, .next ou a base local. Confirmar privadamente a rotação Neon já assinalada e manter contas internas, isolamento, autorização técnica e quotas gratuitas.
5. Validar com uma conta interna: demonstração -> PDF completo -> cronologia, mapa, referências E#, datas desconhecidas e anexo. Depois conferir um dossiê autorizado real, uma síntese desatualizada e ausência de evidências, preservando avisos. Confirmar consumo/CPU Free e acesso das três contas antes de considerar concluído.

O PDF em output/pdf/ tem nove páginas e é um exemplo fictício, sem fontes ou modelo ao vivo. Imagens de cronologia/mapa acompanham-no. A aplicação gera os gráficos a partir do snapshot atual de cada investigação, sem novas consultas ao descarregar.

Não seguem chaves, contas, base, histórico privado, dependências ou builds. A versão pública não foi alterada pelo Gonçalo nesta revisão. Não enviar segredos no chat. Password própria mantém-se adiada.
