# Passos privados da pessoa — instalação online

## Primeiro: corrigir a ligação da interface

O novo link é https://websecai-frontend.websecai-estg.workers.dev/login. Abre, mas a API ainda aceita apenas a origem anterior. No Render, websecaiapi → Environment → Edit, guardar:

```text
CORS_ORIGINS=https://websecai-frontend.websecai-estg.workers.dev
APP_ALLOWED_EMAILS=<lista privada dos dois emails autorizados>
```

Não alterar as URLs Neon nem JWT_SECRET. Escolher Save, rebuild, and deploy e guardar. Aguardar Live e avisar «configuração guardada», sem valores ou capturas de credenciais. A revisão automática bloqueou o controlo de edição/revelação; a pessoa conclui no painel. O terceiro email ainda não foi indicado.

## Criar as contas WebSecAI

Contas Neon/Cloudflare/Render/GitHub são diferentes das contas da aplicação. Email autorizado não significa conta criada. O backend de produção fecha o registo público, apesar de ainda existir o botão Criar conta na interface.

Nesta máquina, Tiago abre pessoalmente Criar_Conta_WebSecAI.cmd e Criar_Conta_Goncalo.cmd em outputs. Cada launcher pede a ligação Neon direta em campo oculto e o nome/password duas vezes através do script existente. Selecionar **WebSecCheckAI → websecai-validacao → Connect → pooling desligado**. A ligação não é guardada pelo helper; não a enviar no chat. Não executar estes launchers através do assistente. Se já existir .env.production, usar o script normal com essa configuração privada. Contas existentes são preservadas; não há reset de password.

Para outra máquina, preparar privadamente codigo/backend/.env.production com o destino autorizado e executar pessoalmente `python scripts/provision_group.py`. O README/VALIDACAO_PUBLICACAO descrevem as variáveis; não copiar configurações do colega nem enviar ficheiros privados. A conta do Gonçalo deve ter password própria, introduzida por ele ou combinada diretamente entre as pessoas por um canal privado, sem o modelo.

Depois, cada um abre /login, introduz o seu username/email e a sua password. Não partilhar uma sessão. Gonçalo não precisa de receber a ligação Neon, passwords dos fornecedores ou acesso administrativo para usar a app. As investigações de cada conta continuam privadas.

## O que ainda precisa de aceitação

- Entrar e executar a demonstração fictícia, abrir histórico e PDF, recarregar e verificar isolamento entre duas contas. Confirmar também após cold start. Até agora essa aceitação completa foi local com contas sintéticas.
- URLhaus: obter/guardar a Auth-Key apenas no formulário oculto local; responder «URLhaus guardada». Só depois, no máximo duas consultas totais ao fornecedor oficial através de scripts/validar_urlhaus.py. Zero feitas até agora. Chave local não é automaticamente chave no Render.
- Tavily/Groq: limites online continuam a zero; nenhuma chamada real sem pequeno orçamento humano confirmado. Não repetir lotes antigos.
- Resolver o consumo CPU do frontend antes de declarar Free sustentado aceite (P50 observado 18,322 ms perante limite 10 ms). Nenhum upgrade autorizado. Ver relatório.

Entregar ao Gonçalo ENTREGA_AO_GONCALO.md, o link do ramo/PR e o pacote de alterações. Não enviar .env, bases, chaves, cookies, auth dirs, tokens ou logs. Os launchers de autorização/configuração em outputs são ajudas locais desta máquina, não um pacote portátil para o colega.
