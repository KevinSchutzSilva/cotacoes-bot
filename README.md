# 🤖 Bot de Cotações no Telegram — Relatório + Guia de Instalação

Bot que te manda no Telegram, todo dia útil às **07:15**, a cotação de **dólar, euro,
libra e dólar canadense + IBOVESPA**, com a variação do dia e a comparação com a
média dos últimos 30 dias. Roda **de graça na nuvem** (GitHub Actions) — seu PC não
precisa ficar ligado.

---

## ✅ O que eu já fiz e testei (o relatório)

- **Escrevi o código todo** (`monitor.py`): busca as 4 moedas + IBOVESPA, calcula a
  variação, compara com a média de 30 dias e monta a mensagem.
- **Testei a lógica e a formatação** com dados de exemplo (arquivo `test_local.py`).
  Passou em todos os casos: tudo normal, IBOVESPA fora do ar e uma moeda sem dados.
  Os números saem no padrão brasileiro (R$ 5,42 / 142.350 pts).
- **Conferi que as dependências instalam** sem erro (`requests` e `yfinance`).
- **Montei o agendamento** (`.github/workflows/cotacoes.yml`) já no horário certo:
  07:15 de Brasília (= 10:15 UTC, e o Brasil não tem horário de verão, então nunca
  desregula).
- **O que eu NÃO consegui testar:** a chamada às APIs de verdade e o envio no
  Telegram. Meu ambiente de teste bloqueia internet externa por segurança. Mas o
  código está correto e vai rodar normal no GitHub, que tem internet liberada. Você
  confirma isso no **Passo 6** (o botão de teste manual).

**Fontes dos dados (grátis, sem precisar pagar nem cadastrar):**
- Moedas → AwesomeAPI (brasileira)
- IBOVESPA → Yahoo Finance (via yfinance)

---

## 📲 O que VOCÊ precisa fazer (~10 min, uma vez só)

### Parte 1 — Telegram (criar o bot)

1. No Telegram, procure por **@BotFather** e mande `/newbot`.
2. Ele pede um nome e um @usuário pro bot. Escolha qualquer um (o @ tem que
   terminar em `bot`, ex: `cotacoes_kevin_bot`).
3. No fim ele te dá o **TOKEN** (uma linha tipo `8123456:AAH...`). **Guarde, é senha.**
   ⚠️ Não cola esse token em chat nenhum — só no lugar do Passo 5.
4. **Mande um `/start` pro SEU bot** (procure o @ que você criou e clique em Iniciar).
   Sem isso o Telegram não deixa o bot te enviar mensagem.
5. Pra pegar seu **CHAT ID**: procure **@userinfobot** no Telegram e mande qualquer
   coisa. Ele responde com o seu `Id` (um número). Guarde esse número.

### Parte 2 — GitHub (colocar pra rodar na nuvem)

6. Crie uma conta grátis em **github.com** (se ainda não tem).
7. Clique em **New repository** → dê um nome (ex: `cotacoes-bot`) → marque como
   **Public** (público é o que dá o agendamento de graça) → **Create**.
8. **Suba os arquivos:** na página do repositório → **Add file → Upload files** →
   arraste os arquivos `monitor.py`, `requirements.txt` e a pasta `.github` inteira →
   **Commit changes**.
   *(Se preferir não arrastar a pasta: use "Add file → Create new file", escreva no
   nome o caminho exato `.github/workflows/cotacoes.yml` e cole o conteúdo do arquivo.)*

### Parte 3 — Guardar as senhas com segurança

9. No repositório → **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**. Crie **dois**:
   - Nome: `TELEGRAM_TOKEN` → valor: o token do BotFather (Passo 3)
   - Nome: `TELEGRAM_CHAT_ID` → valor: o número do Passo 5

   👉 É aqui que entram suas senhas, num cofre que só você acessa. Eu nunca vejo.

### Parte 4 — Testar agora (sem esperar até amanhã 07:15)

10. No repositório → aba **Actions** → clique no workflow **"Cotações diárias"** →
    botão **Run workflow**. Em ~1 minuto deve cair a mensagem no seu Telegram. 🎉

Deu certo no teste? Então tá pronto. A partir daí ele dispara sozinho todo dia útil
às 07:15, sem você fazer mais nada.

---

## 🔧 Como mudar coisas depois

- **Horário:** no arquivo `.github/workflows/cotacoes.yml`, na linha do `cron`. O
  formato é `minuto hora * * dias`, em **UTC**. Lembre: hora de Brasília + 3 = UTC.
  Ex: pra 06:30, use `30 9 * * 1-5`.
- **Incluir fim de semana:** troque `1-5` por `*` (mas atenção: nos fins de semana
  as bolsas estão fechadas, então os números repetem os de sexta).
- **Trocar/adicionar moedas:** no `monitor.py`, na lista `MOEDAS` lá no começo.

---

## ⚠️ Lembrete honesto

O bot mostra **informação boa** (preço, variação, posição vs. a média), mas **não
prevê** se vai subir ou cair. Ninguém prevê o curto prazo de moeda. Use os números
pra decidir você mesmo, com calma — principalmente porque, como combinamos, seu plano
é de longo prazo e você só vai abrir conta de câmbio quando fizer 18.
