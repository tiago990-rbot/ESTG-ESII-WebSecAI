# Validação URLhaus — 22/10/2026

## Resultado efetivo

**Aceitação ao vivo pendente. Zero consultas de indicadores ao fornecedor.** A verificação de estado mais recente devolveu `not_configured`. Não foi lida nem apresentada qualquer chave, ficheiro privado de configuração, clipboard ou campo de credenciais. O formulário foi lançado para introdução humana; isso não comprova que tenha sido preenchido.

| Aspeto | Estado |
| --- | --- |
| Adaptador e formulário oculto | Já existiam no ZIP |
| Configuração presente | Não, na última verificação |
| Autenticação comprovada | Não |
| Resposta real sem correspondências | Não testada |
| Correspondência positiva real | Não testada |
| Positivos, ausência de resultados e erros | Testes controlados; não são aceitação real |
| Tavily/Groq durante esta passagem | Zero chamadas reais |

## Base e ambiente

- Código do ZIP v2, sem usar o GitHub como base. Manifesto original: 138 ficheiros verificados, zero diferenças.
- SHA-256 do ZIP: `df9059a722c9b426fb573ba8f1b5bb801009d7ebaa8e7672abf19da0a53fde63`.
- Revisão local preparada: `8d8cf77199ee0bfc31b4bd5ac610a8c55a524053`, ramo `codex/publicacao-gratuita`.
- Windows, Python 3.12.14, httpx 0.28.1. Verificação inicial isolada em `2026-10-22T12:57:22.511555+00:00`: chave ausente, zero pedidos.
- A conversa partilhada não abriu no assistente. Foram usados os documentos do ZIP.

## Documentação oficial verificada

A [documentação URLhaus](https://urlhaus-api.abuse.ch/) exige o cabeçalho `Auth-Key` e indica obtenção gratuita da chave no [portal abuse.ch](https://auth.abuse.ch/). A consulta de host usa POST para `/v1/host/`, com o parâmetro `host`. `no_results` é um estado documentado da resposta. Não foi assumida uma quota numérica que a documentação consultada não especifica. A pessoa deve confirmar que a sua conta e utilização académica têm acesso gratuito, sem subscrição paga.

## Próximo passo privado da pessoa

1. Obter a Auth-Key nos portais oficiais e confirmar as condições gratuitas.
2. Abrir `codigo/Configurar_APIs.cmd`, preencher apenas URLhaus no campo oculto, confirmar o acesso gratuito e guardar. Tavily/Groq podem ficar vazias.
3. Responder apenas «URLhaus guardada». Não enviar a chave, o `.env` ou capturas dos campos.

Depois, a partir de `codigo/backend`, executar uma vez:

```powershell
& .\.venv\Scripts\python.exe scripts/validar_urlhaus.py
```

O comando carrega a configuração internamente e invoca apenas `providers.guarded(providers.urlhaus, "https://example.com/")`. Consulta o fornecedor oficial sobre o host reservado; não resolve/visita esse alvo nem descarrega malware. Não cria uma investigação completa e não chama outros módulos.

O script apresenta apenas UTC, presença de configuração, estado, mensagem segura, contagem e indicação de autenticação. Reserva cada tentativa antes do pedido em `.cache/urlhaus-validation/`, recusa a terceira e não repete automaticamente em caso de erro. Não apagar esse registo para repetir esta passagem. Os resultados reais seguros podem ser acrescentados a este relatório; nenhum existe ainda.

## Como interpretar

- `configured=true`: existe um valor; não comprova autenticação.
- `authenticated=true`: foi recebida uma resposta interpretável com `query_status` oficial reconhecido nesta consulta. Não valida todas as operações nem cobertura positiva.
- `no_results` autenticado: não houve correspondências para esta consulta naquele momento; não prova segurança.
- `access_denied`: confirmar privadamente chave, conta, permissões e plano; não repetir por rotina.
- `rate_limited` ou condições/custos pouco claros: parar.
- HTTP 404 isolado: o novo comando distingue-o de uma resposta autenticada sem resultados.

## Testes executados

A suite recebida passou com 98 testes antes de alterações. Após adaptação: 105 aprovados/1 omitido em SQLite e 106 aprovados em PostgreSQL local real. Os novos testes do comando URLhaus provaram, com respostas controladas, a reserva máxima de duas tentativas, a ausência da chave na saída e a distinção entre `no_results` interpretável e HTTP 404. O adaptador original não precisou de alteração.

Falta: configuração humana, até duas consultas reais no total, registo UTC/estado/contagem dos pedidos efetivos e confirmação das condições da conta. Nenhum teste externo Tavily/Groq foi realizado ou autorizado por inferência.

Revisão final de regressão: 113 testes aprovados em PostgreSQL local. A publicação remota não acrescentou consultas URLhaus: mantém-se zero.
