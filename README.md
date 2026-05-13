# 🎭 Drama Certo Bot

Bot do Telegram para venda e entrega automática de dramas curtos via Pix.

---

## 📁 Estrutura dos arquivos

```
drama_certo_bot/
├── bot.py           # Arquivo principal do bot
├── dramas.py        # Catálogo de dramas (edite aqui!)
├── pagamento.py     # Integração com Mercado Pago
├── database.py      # Banco de dados de pedidos
├── requirements.txt # Dependências
└── .env.example     # Modelo de variáveis de ambiente
```

---

## ⚙️ Configuração inicial

### 1. Descubra seu ID do Telegram
- Abra seu bot no Telegram
- Mande o comando `/meuid`
- Copie o número que aparecer

### 2. Adicione seus dramas
- Abra o arquivo `dramas.py`
- Para cada drama, coloque o `file_id` do vídeo

**Como pegar o file_id de um vídeo:**
1. Envie o vídeo para o bot @RawDataBot no Telegram
2. Ele retorna os detalhes do arquivo
3. Copie o valor de `file_id`

### 3. Configure as variáveis no Railway
No painel do Railway, vá em **Variables** e adicione:

| Variável | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token do BotFather |
| `MP_ACCESS_TOKEN` | Token do Mercado Pago |
| `ADMIN_ID` | Seu ID do Telegram |

---

## 🚀 Como fazer deploy no Railway

1. Crie uma conta em **railway.app**
2. Clique em **"New Project"** → **"Deploy from GitHub"**
3. Faça upload dos arquivos ou conecte o GitHub
4. Adicione as variáveis de ambiente
5. O bot sobe automaticamente!

---

## 💰 Fluxo de vendas

1. Cliente manda `/start`
2. Escolhe um drama
3. Recebe o código Pix
4. Paga e manda o comprovante
5. Você recebe notificação e clica **"Confirmar e Entregar"**
6. Bot entrega o vídeo automaticamente!

---

## 📞 Suporte

Caso tenha dúvidas, entre em contato com o suporte do Drama Certo.
