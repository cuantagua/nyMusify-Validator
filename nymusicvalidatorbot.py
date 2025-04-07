from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from db_functions import validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id, add_coupon, add_file
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext,
    CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
)
import sqlite3

UPLOAD, CREATE_COUPON, ASSIGN_FILE = range(3)

ADMIN_IDS = [851194595]

DB = "bot_database.db"

TOKEN = '7987679597:AAHK4k-8kzUmDBfC9_R1cVroDqXEDqz6sB4'

# Estados de conversación
REDEEM = 1

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
    query.answer()

    if query.data == 'redeem':
        await query.message.reply_text("🔑 Ingresa el código de cupón:")
        return REDEEM

    elif query.data == 'my_files':
        await query.message.reply_text("📁 Aquí verás tus archivos redimidos. (Función en desarrollo)")

    elif query.data == 'help':
        await query.message.reply_text(
            "ℹ️ Puedes usar un cupón para acceder a tus archivos de audio.\n"
            "Presiona 'Redimir cupón' para comenzar."
        )

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
    #elif any_redemption_for_coupon(user_input):  # Esta función debes implementarla si deseas verificar si otro ya lo usó
        #await update.message.reply_text("⚠️ Este cupón ya fue usado. Revisa el código o intenta con otro.")
        #return ConversationHandler.END
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
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

from database import init_db

init_db()

#Menu de admin
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 No tienes permisos para acceder a este menú.")
        return

    keyboard = [
        [InlineKeyboardButton("📤 Subir nuevo archivo", callback_data='upload_file')],
        [InlineKeyboardButton("🎫 Crear nuevo cupón", callback_data='create_coupon')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Menú de administrador:", reply_markup=reply_markup)
    
from db_functions import add_file  # Función que ahora veremos

# Estados

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        await query.message.reply_text("🚫 No autorizado.")
        return ConversationHandler.END

    if query.data == 'upload_file':
        await query.message.reply_text("📤 Envía el archivo de audio (WAV o MP3):")
        return UPLOAD

    elif query.data == 'create_coupon':
        await query.message.reply_text("📝 Escribe el código del nuevo cupón (formato XXX-XXX):")
        return CREATE_COUPON

    elif query.data == 'assign_file':
        await query.message.reply_text("📎 Esta función estará disponible pronto.")
        return ConversationHandler.END

    return ConversationHandler.END


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user_id = update.effective_user.id

    if not doc.mime_type.startswith('audio/'):
        await update.message.reply_text("❌ Solo se aceptan archivos de audio (WAV o MP3).")
        return ConversationHandler.END

    name = doc.file_name
    file_id = doc.file_id

    add_file(name, file_id)
    await update.message.reply_text(f"✅ Archivo '{name}' guardado con éxito.")
    return ConversationHandler.END

async def handle_create_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()

    # Validar formato: 3 letras o números - 3 letras o números
    import re
    if not re.match(r"^[A-Z0-9]{3}-[A-Z0-9]{3}$", code):
        await update.message.reply_text("❌ Código inválido. Usa el formato XXX-XXX (letras y números).")
        return CREATE_COUPON

    success = add_coupon(code)
    if success:
        await update.message.reply_text(f"✅ Cupón creado: {code}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("⚠️ Ese cupón ya existe. Prueba con otro código.")
        return CREATE_COUPON



# Iniciar la aplicación
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversación para redimir cupón
    redeem_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_handler)],
        states={
            REDEEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_coupon)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    admin_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_button_handler)],
    states={
        UPLOAD: [MessageHandler(filters.Document.ALL, handle_file_upload)],
        CREATE_COUPON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_coupon)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(redeem_conv)
    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("admin", admin_menu))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == '__main__':
    main()


