from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
)
from db_functions import (
    validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id, add_coupon, add_file, init_db, get_redeemed_files_by_user
)
from admin_functions import handle_file_upload, handle_generate_code, handle_code_quantity
import sqlite3

# Inicialización de la base de datos
init_db()

# Estados de conversación
UPLOAD, GENERATE_CODE, ASK_CODE_QUANTITY, REDEEM = range(4)

# Configuración
ADMIN_IDS = [851194595]
TOKEN = '7987679597:AAHK4k-8kzUmDBfC9_R1cVroDqXEDqz6sB4'

cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("❌ Cancelar")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Menú principal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¡Bienvenido! ¿Qué deseas hacer?", reply_markup=reply_markup)

# Manejo de botones del menú
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'redeem':
        await query.message.reply_text("🔑 Ingresa el código de cupón:", reply_markup=cancel_keyboard)
        return REDEEM
    elif query.data == 'my_files':
        await show_redeemed_files(update, context)
        return ConversationHandler.END
    elif query.data == 'help':
        await query.message.reply_text("ℹ️ Usa un cupón para acceder a tus archivos.\nPresiona 'Redimir cupón' para comenzar.")
        return ConversationHandler.END

# Proceso de redención de cupón
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

# Cancelar conversación
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("❌ Operación cancelada.", reply_markup=reply_markup)
    return ConversationHandler.END

# Mostrar archivos redimidos
async def show_redeemed_files(update, context, order_by="recent", page=0):
    user_id = update.effective_user.id
    files, total = get_redeemed_files_by_user(user_id, order_by, limit=5, offset=page * 5)

    if not files:
        await update.message.reply_text("No has redimido ningún archivo todavía.")
        return

    keyboard = [
        [InlineKeyboardButton(f"📥 {name}", callback_data=f"getfile_{index}")]
        for index, (name, _, _) in enumerate(files)
    ]
    await update.message.reply_text("📦 Archivos redimidos:", reply_markup=InlineKeyboardMarkup(keyboard))

# Iniciar la aplicación
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_upload, pattern="^upload_file$")],
        states={
            UPLOAD: [MessageHandler(filters.ATTACHMENT, handle_file_upload)],
            GENERATE_CODE: [CallbackQueryHandler(handle_generate_code, pattern="^(generate_code|finish_upload)$")],
            ASK_CODE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_quantity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    redeem_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_handler, pattern="^(redeem|my_files|help)$")],
        states={
            REDEEM: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancelar$"), redeem_coupon)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(redeem_conv)

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == '__main__':
    main()


