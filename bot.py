import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from pagamento import criar_pix
from database import salvar_pedido, buscar_pedido_por_usuario, marcar_entregue, listar_pedidos_pendentes
from dramas import CATALOGO

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8552238459:AAGbv-jU0DTeg9p9nO3f2kP0qtKYCYnlvjg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Coloque seu ID do Telegram aqui


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagem de boas-vindas com catálogo."""
    user = update.effective_user
    texto = (
        f"Olá, {user.first_name}! 👋\n\n"
        "🎭 Bem-vindo ao *Drama Certo*!\n\n"
        "Aqui você encontra os melhores dramas curtos.\n"
        "Escolha um drama abaixo para comprar:"
    )
    keyboard = []
    for drama_id, drama in CATALOGO.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{drama['nome']} — R$ {drama['preco']:.2f}",
                callback_data=f"comprar_{drama_id}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=reply_markup)


async def selecionar_drama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quando o cliente clica num drama, gera o Pix."""
    query = update.callback_query
    await query.answer()

    drama_id = query.data.replace("comprar_", "")
    drama = CATALOGO.get(drama_id)

    if not drama:
        await query.edit_message_text("Drama não encontrado. Use /start para ver o catálogo.")
        return

    user_id = query.from_user.id
    user_name = query.from_user.first_name

    # Gera o Pix
    pix_data = criar_pix(
        valor=drama["preco"],
        descricao=f"Drama Certo - {drama['nome']}",
        drama_id=drama_id,
        user_id=user_id
    )

    if not pix_data:
        await query.edit_message_text(
            "❌ Erro ao gerar o Pix. Tente novamente ou fale com o suporte."
        )
        return

    # Salva o pedido no banco
    salvar_pedido(
        user_id=user_id,
        user_name=user_name,
        drama_id=drama_id,
        drama_nome=drama["nome"],
        payment_id=pix_data["id"],
        valor=drama["preco"]
    )

    texto = (
        f"🎭 *{drama['nome']}*\n"
        f"💰 Valor: R$ {drama['preco']:.2f}\n\n"
        f"📲 *Pague via Pix:*\n\n"
        f"`{pix_data['pix_copia_cola']}`\n\n"
        f"_(Toque no código acima para copiar)_\n\n"
        f"✅ Após pagar, envie o *comprovante aqui* que entregamos seu drama automaticamente!\n\n"
        f"⏳ O Pix expira em 30 minutos."
    )

    await query.edit_message_text(texto, parse_mode="Markdown")


async def receber_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quando o cliente manda uma imagem (comprovante)."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    pedido = buscar_pedido_por_usuario(user_id)

    if not pedido:
        await update.message.reply_text(
            "Não encontrei nenhum pedido pendente para você.\n"
            "Use /start para ver o catálogo e fazer um pedido!"
        )
        return

    drama = CATALOGO.get(pedido["drama_id"])
    if not drama:
        await update.message.reply_text("❌ Erro interno. Por favor, fale com o suporte.")
        return

    # Avisa o cliente
    await update.message.reply_text(
        "📋 *Comprovante recebido!*\n\n"
        "Estamos verificando seu pagamento... ⏳\n"
        "Você receberá o drama em instantes!",
        parse_mode="Markdown"
    )

    # Notifica o admin para verificação manual
    if ADMIN_ID:
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            keyboard = [[
                InlineKeyboardButton(
                    "✅ Confirmar e Entregar",
                    callback_data=f"entregar_{user_id}_{pedido['drama_id']}"
                ),
                InlineKeyboardButton(
                    "❌ Rejeitar",
                    callback_data=f"rejeitar_{user_id}"
                )
            ]]
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔔 *Novo comprovante recebido!*\n\n"
                    f"👤 Cliente: {user_name} (ID: {user_id})\n"
                    f"🎭 Drama: {pedido['drama_nome']}\n"
                    f"💰 Valor: R$ {pedido['valor']:.2f}\n\n"
                    f"Confirme o pagamento para entregar o drama:"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Erro ao notificar admin: {e}")


async def admin_entregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin confirma pagamento e o bot entrega o drama."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("Você não tem permissão para isso.", show_alert=True)
        return

    partes = query.data.split("_")
    acao = partes[0]
    cliente_id = int(partes[1])

    if acao == "entregar":
        drama_id = partes[2]
        drama = CATALOGO.get(drama_id)

        if not drama:
            await query.edit_message_text("❌ Drama não encontrado no catálogo.")
            return

        try:
            # Envia o vídeo para o cliente
            await context.bot.send_message(
                chat_id=cliente_id,
                text=(
                    f"🎉 *Pagamento confirmado!*\n\n"
                    f"Aqui está seu drama: *{drama['nome']}* 🎭\n\n"
                    f"Aproveite! ❤️"
                ),
                parse_mode="Markdown"
            )

            # Envia o link do canal privado do drama
            await context.bot.send_message(
                chat_id=cliente_id,
                text=(
                    f"🔗 *Acesse seu canal exclusivo:*\n\n"
                    f"{drama['canal']}\n\n"
                    f"⚠️ Este link é pessoal, não compartilhe com ninguém!"
                ),
                parse_mode="Markdown"
            )

            marcar_entregue(cliente_id)
            await query.edit_message_text(
                f"✅ Drama *{drama['nome']}* entregue para o cliente {cliente_id}!",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Erro ao entregar drama: {e}")
            await query.edit_message_text(f"❌ Erro ao entregar: {e}")

    elif acao == "rejeitar":
        try:
            await context.bot.send_message(
                chat_id=cliente_id,
                text=(
                    "❌ *Comprovante não confirmado.*\n\n"
                    "Não conseguimos validar seu pagamento.\n"
                    "Por favor, envie um comprovante mais legível ou entre em contato com o suporte."
                ),
                parse_mode="Markdown"
            )
            await query.edit_message_text("❌ Comprovante rejeitado. Cliente foi notificado.")
        except Exception as e:
            await query.edit_message_text(f"Erro: {e}")


async def meu_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para o admin descobrir seu ID."""
    await update.message.reply_text(f"Seu ID é: `{update.effective_user.id}`", parse_mode="Markdown")


async def admin_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista pedidos pendentes (só admin)."""
    if update.effective_user.id != ADMIN_ID:
        return

    pedidos = listar_pedidos_pendentes()
    if not pedidos:
        await update.message.reply_text("Nenhum pedido pendente no momento.")
        return

    texto = "📋 *Pedidos pendentes:*\n\n"
    for p in pedidos:
        texto += (
            f"👤 {p['user_name']} (ID: {p['user_id']})\n"
            f"🎭 {p['drama_nome']} — R$ {p['valor']:.2f}\n"
            f"🕐 {p['criado_em']}\n\n"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("meuid", meu_id))
    app.add_handler(CommandHandler("pedidos", admin_pedidos))
    app.add_handler(CallbackQueryHandler(selecionar_drama, pattern="^comprar_"))
    app.add_handler(CallbackQueryHandler(admin_entregar, pattern="^entregar_|^rejeitar_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receber_comprovante))

    logger.info("Bot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
