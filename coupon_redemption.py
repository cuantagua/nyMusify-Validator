from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from db_functions import validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id

async def redeem_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().upper()
    user_id = update.effective_user.id

    file_ids = validate_coupon(user_input)

    if not file_ids:
        await update.message.reply_text("❌ Cupón inválido. Verifica el código e inténtalo de nuevo.")
        return ConversationHandler.END

    if coupon_used_by_user(user_id, user_input):
        await update.message.reply_text("🔁 Ya redimiste este cupón. Aquí están tus archivos:")
    else:
        register_redemption(user_id, user_input)
        await update.message.reply_text("✅ ¡Cupón válido! Aquí tienes tus archivos:")

    for file_id in file_ids:
        archivo = get_file_by_id(file_id)
        if archivo:
            name, telegram_file_id = archivo
            await update.message.reply_document(telegram_file_id, caption=f"🎵 {name}")

    return ConversationHandler.END