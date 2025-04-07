from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ContextTypes
from db_functions import validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)

UPLOAD, CREATE_COUPON, ASSIGN_FILE = range(3)

ADMIN_IDS = [851194595]

TOKEN = '7987679597:AAHK4k-8kzUmDBfC9_R1cVroDqXEDqz6sB4'

# Estados de conversación
REDEEM = 1

# Menú principal
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("¡Bienvenido! ¿Qué deseas hacer?", reply_markup=reply_markup)

# Manejo de botones del menú
def menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'redeem':
        query.message.reply_text("🔑 Ingresa el código de cupón:")
        return REDEEM

    elif query.data == 'my_files':
        query.message.reply_text("📁 Aquí verás tus archivos redimidos. (Función en desarrollo)")

    elif query.data == 'help':
        query.message.reply_text(
            "ℹ️ Puedes usar un cupón para acceder a tus archivos de audio.\n"
            "Presiona 'Redimir cupón' para comenzar."
        )

    return ConversationHandler.END

# Proceso de redención de cupón
def redeem_coupon(update: Update, context: CallbackContext):
    user_input = update.message.text.strip().upper()
    user_id = update.effective_user.id

    file_ids = validate_coupon(user_input)

    if not file_ids:
        update.message.reply_text("❌ Cupón inválido. Verifica el código e inténtalo de nuevo.")
        return ConversationHandler.END

    if coupon_used_by_user(user_id, user_input):
        update.message.reply_text("🔁 Ya redimiste este cupón. Aquí están tus archivos:")
    elif any_redemption_for_coupon(user_input):  # Esta función debes implementarla si deseas verificar si otro ya lo usó
        update.message.reply_text("⚠️ Este cupón ya fue usado. Revisa el código o intenta con otro.")
        return ConversationHandler.END
    else:
        register_redemption(user_id, user_input)
        update.message.reply_text("✅ ¡Cupón válido! Aquí tienes tus archivos:")

    for file_id in file_ids:
        archivo = get_file_by_id(file_id)
        if archivo:
            name, telegram_file_id = archivo
            update.message.reply_document(telegram_file_id, caption=f"🎵 {name}")

    return ConversationHandler.END

# Cancelar conversación
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Operación cancelada.")
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(redeem_conv)
    app.add_handler(CommandHandler("admin", admin_menu))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == '__main__':
    main()


from db_functions import add_file  # Función que ahora veremos

# Estados
UPLOAD = range(1)

def admin_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        query.message.reply_text("🚫 No autorizado.")
        return ConversationHandler.END

    if query.data == 'upload_file':
        query.message.reply_text("📤 Envía el archivo de audio (WAV o MP3):")
        return UPLOAD

    # Opciones adicionales se programarán luego

    return ConversationHandler.END

def handle_file_upload(update: Update, context: CallbackContext):
    doc = update.message.document
    user_id = update.effective_user.id

    if not doc.mime_type.startswith('audio/'):
        update.message.reply_text("❌ Solo se aceptan archivos de audio (WAV o MP3).")
        return ConversationHandler.END

    name = doc.file_name
    file_id = doc.file_id

    add_file(name, file_id)
    update.message.reply_text(f"✅ Archivo '{name}' guardado con éxito.")
    return ConversationHandler.END

admin_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_button_handler)],
    states={
        UPLOAD: [MessageHandler(filters.Document.ALL, handle_file_upload)],
        CREATE_COUPON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_coupon)],
    },
    fallbacks=[],
)


def add_file(name, file_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO files (name, file_id) VALUES (?, ?)", (name, file_id))
    conn.commit()
    conn.close()

def admin_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        query.message.reply_text("🚫 No autorizado.")
        return ConversationHandler.END

    if query.data == 'upload_file':
        query.message.reply_text("📤 Envía el archivo de audio (WAV o MP3):")
        return UPLOAD

    elif query.data == 'create_coupon':
        query.message.reply_text("📝 Escribe el código del nuevo cupón (formato XXX-XXX):")
        return CREATE_COUPON

    elif query.data == 'assign_file':
        query.message.reply_text("📎 Esta función estará disponible pronto.")
        return ConversationHandler.END

    return ConversationHandler.END


from db_functions import add_coupon

def handle_create_coupon(update: Update, context: CallbackContext):
    code = update.message.text.strip().upper()

    # Validar formato: 3 letras o números - 3 letras o números
    import re
    if not re.match(r"^[A-Z0-9]{3}-[A-Z0-9]{3}$", code):
        update.message.reply_text("❌ Código inválido. Usa el formato XXX-XXX (letras y números).")
        return CREATE_COUPON

    success = add_coupon(code)
    if success:
        update.message.reply_text(f"✅ Cupón creado: {code}")
        return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ Ese cupón ya existe. Prueba con otro código.")
        return CREATE_COUPON

