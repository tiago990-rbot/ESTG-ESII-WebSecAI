# Passos atuais da pessoa

Seguir CRIAR_CONTAS_PASSO_A_PASSO.md: rotação Neon, ligações pooled/direta no Render e criação privada de contas. CORS já está corrigido. A revisão v5 foi publicada. Contas e aceitação autenticada online ainda não confirmadas.

# Criar as contas WebSecAI — passos privados

## 1. Alterar primeiro a password Neon exposta

A página Neon **Roles** da branch **websecai-validacao**, projeto **WebSecCheckAI**, ficou aberta no menu da role neondb_owner. Clica pessoalmente em **Reset password** e confirma. Esta é a password da base, diferente das passwords das contas WebSecAI. Não envies valores ou capturas.

Se a ligação exposta foi copiada de outra branch, roda também a credencial nessa branch. A gestão de roles é por branch; não assumir que alterar uma altera todas. Não eliminar roles ou bases.

Documentação oficial: https://neon.com/docs/manage/roles.

## 2. Atualizar as ligações privadas do Render

No Neon, na mesma branch websecai-validacao, abre **Connect → Connection string**, confirma a base neondb e a role correta.

1. Liga **Connection pooling** e copia a ligação nova completa.
2. No Render, serviço **websecaiapi → Environment → Edit**, substitui **DATABASE_URL** pela ligação nova.
3. Volta ao Neon, desliga **Connection pooling** e copia a ligação direta da mesma branch/base/role.
4. Substitui **DATABASE_MIGRATION_URL** no Render pela ligação direta.
5. Confirma privadamente que **APP_ALLOWED_EMAILS** contém os dois emails autorizados: <lista privada dos dois emails autorizados>. Não acrescentar outras pessoas por rotina.
6. Mantém **CORS_ORIGINS=https://websecai-frontend.websecai-estg.workers.dev** e preserva JWT_SECRET e os restantes campos. Não alteres limites de fornecedores, planos ou serviços.
7. Escolhe **Save, rebuild, and deploy**, guarda e aguarda **Live/Deploy succeeded**. A alteração pode interromper temporariamente a ligação à base até os valores estarem atualizados.

Não copies valores para código, ficheiros .cmd, chat, capturas ou Git. O assistente não precisa de conhecer as ligações.

## 3. Criar a tua conta

A janela **WebSecAI - criar contas do grupo em privado** apresenta um menu. Escolhe **1** para Tiago. Este menu executa o procedimento existente de provisionamento; não abre o registo público.

1. Quando o terminal pedir **Ligacao direta Neon (oculta)**, cola a ligação com pooling desligado e carrega em Enter. É normal não aparecer texto. Não coles a ligação no editor do ficheiro.
2. Introduz um nome de utilizador entre 3 e 80 caracteres.
3. Introduz uma password WebSecAI própria entre 6 e 128 caracteres e repete-a. Escolhe uma password longa e diferente da password Neon. O terminal não a mostra.
4. Aguarda **Conta criada**. Se aparecer **Conta existente preservada**, não foi criada outra nem alterada a password existente.
5. Se houver erro, lê a mensagem genérica e confirma privadamente branch/ligação/dados. Não envies valores. Não repetir consultas externas para tentar resolver a conta.

Se a janela já estiver fechada, abre o **Explorador de Ficheiros** e executa por duplo clique **outputs/Criar_Contas_Grupo.cmd**. Clicar num link desse ficheiro no Codex pode abrir o editor; isso não executa o programa. O menu e os launchers são locais desta máquina, não são o pacote portátil para o Gonçalo.

Se existir .env.production, o helper preserva-o e pede para usar o procedimento normal `codigo/backend/scripts/provision_group.py`, com configuração privada preparada pela pessoa. O assistente não lê esse ficheiro nem o executa com dados reais.

## 4. Criar a conta do Gonçalo

No mesmo menu escolhe **2**. Repete o procedimento com um username e uma password próprios para ele. O email da conta já está selecionado no helper. Se ele estiver contigo, deixa-o introduzir pessoalmente a password; caso contrário, combina os dados por um canal privado entre pessoas. Não enviar a ligação Neon ao colega apenas para usar a app. O helper preserva contas existentes e não redefine passwords.

O terceiro email ainda não foi identificado. Não criar uma conta coletiva nem partilhar sessões. Cada conta vê apenas as suas investigações.

## 5. Entrar e confirmar o funcionamento

Abrir **https://websecai-frontend.websecai-estg.workers.dev/login**, introduzir email/username e password WebSecAI. A interface deve explicar o acesso restrito; não existe formulário público para criar contas em produção.

Começar por **Explorar demonstração**, abrir Panorama, Evidências, Cronologia, Mapa de relações e PDF. A demonstração é fictícia e não deve fazer consultas a fornecedores. Confirmar recarregamento/histórico e que a outra conta não acede aos dossiês da primeira. O primeiro acesso pode demorar cerca de um minuto devido à suspensão Render Free.

Confirmar no chat apenas **credencial rodada, Render atualizado e entrei**. Não enviar passwords, tokens, ligações ou capturas com dados sensíveis.

Tavily/Groq mantêm limites a zero até existir pequeno orçamento humano confirmado. URLhaus continua com zero consultas reais nesta passagem e máximo de duas após configuração privada. O ajuste visual não resolve automaticamente o risco CPU do plano Cloudflare Free; ver VALIDACAO_PUBLICACAO.md.
