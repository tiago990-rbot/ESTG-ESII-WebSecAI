# Contas e passwords no site

## Alterar a tua password

Depois de esta revisão estar publicada na API e na interface, entra na app e abre Perfil. Em Alterar palavra-passe, introduz a atual, uma nova exclusiva entre 16 e 128 caracteres e a confirmação. Guarda. Todas as sessões anteriores desta conta deixam de funcionar; escolhe Voltar a entrar e usa a nova password. A conta, o email e as investigações mantêm-se.

Se te esqueceste da atual, o link Esqueci-me da palavra-passe / Receber acesso no login explica como pedir uma reposição ao responsável. Não existe envio automático de emails nem serviço novo contratado. O responsável verifica a identidade da pessoa pelo canal habitual e emite um link privado.

## Convidar o Gonçalo à distância

1. No Explorador de Ficheiros, abre a pasta outputs desta tarefa e executa Gerir_Convites_WebSecAI.cmd por duplo clique. Não o abras num editor nem num terminal cujo conteúdo seja enviado ao assistente.
2. Escolhe 1 — Convite para o Gonçalo.
3. No Neon, escolhe WebSecCheckAI, branch websecai-validacao, Connect, base neondb, Connection string. Desliga Connection pooling e copia a ligação direta. Cola-a apenas no pedido oculto da janela e carrega em Enter. A ligação deve corresponder à instalação online; não usar a branch original por engano.
4. Escolhe um nome de utilizador para a conta dele. O email já é goncalofazendeirocordeiro@gmail.com.
5. Escreve EMITIR para confirmar. O programa cria uma conta pendente, sem password conhecida e sem acesso até ativação. Se a conta já estiver ativa, não a substitui: usa a opção 3, reposição do Gonçalo, depois de confirmar com ele.
6. A janela mostra um link secreto. Copia-o completo, incluindo #token= e todo o final, e envia-o TU ao Gonçalo pelo canal privado habitual. Não enviar ao modelo, ao grupo inteiro, num commit ou numa captura. Não enviar-lhe a ligação Neon.
7. Ele abre o link no site, escolhe a própria password e repete-a. O responsável não recebe nem vê essa password. Depois ele entra no login normal com o email indicado e a password que escolheu.

Convites duram 24 horas. Só funcionam uma vez; emitir outro para a mesma conta invalida o anterior. Recarregar o formulário antes de terminar exige voltar a abrir o link original. O endereço visível perde o fragmento secreto após a página carregar; isso é intencional. Quem tiver o link pode definir a password dessa conta, pelo que deve ser enviado apenas à pessoa certa.

Não é necessário criar uma password padrão. Embora uma conta ativa passe a poder alterar a password pelo Perfil, um convite evita partilhar uma password inicial e impede acesso antes da ativação.

## Repor uma password esquecida

No mesmo programa, opção 2 repõe a conta do Tiago e opção 3 a conta já ativa do Gonçalo. Confirma primeiro a identidade do destinatário. Introduz a ligação privada e escreve EMITIR. O link dura 30 minutos e é de uso único. A password atual e as sessões continuam válidas até o link ser utilizado; nesse momento todas as sessões antigas e os restantes links dessa conta são invalidados. O destinatário define uma password nova no site e entra normalmente; não há login automático nem recuperação por perguntas pessoais.

## Segurança e limites

O registo público mantém-se fechado e os emails continuam sujeitos a APP_ALLOWED_EMAILS no Render. Este fluxo não adiciona membros à allowlist nem dá acesso às investigações dos colegas. Um terceiro membro exige identificar e autorizar o email separadamente.

Links aleatórios de 256 bits; a base guarda apenas SHA-256 do segredo, conta, finalidade, versão e validade. O fragmento não é enviado no pedido da página; a reposição envia o segredo apenas no corpo HTTPS da API. Não é guardado em localStorage. A página declara no-referrer e noindex. A alteração usa o hash PBKDF2 existente sem reduzir o custo e uma versão de sessão persistida no PostgreSQL. São rejeitados links expirados, repetidos, substituídos, de membros removidos e alterações concorrentes.

Não há emails automáticos de notificação. O responsável e o destinatário devem confirmar a conclusão pelo seu canal habitual, sem passwords. O responsável com acesso administrativo à base continua a ter capacidade de gerir contas; esta funcionalidade evita conhecer a password escolhida pelo colega, não remove essa relação de confiança administrativa.

O utilitário anterior Alterar_Password_WebSecAI.cmd fica substituído pelo Perfil e pelos links privados. Não o usar para gerir contas após esta publicação.

Orientação de segurança consultada: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html . Nenhum fornecedor de Threat Intelligence ou IA é necessário para estes fluxos.
