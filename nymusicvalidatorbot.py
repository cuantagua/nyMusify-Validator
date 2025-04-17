from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
)
from db_functions import (
    validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id, add_coupon, add_file, init_db, get_redeemed_files_by_user
)
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

# Cancelar conversación
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("❌ Operación cancelada.", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("❌ Operación cancelada.", reply_markup=reply_markup)

    return ConversationHandler.END

# Menú principal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¡Bienvenido! ¿Qué deseas hacer?", reply_markup=reply_markup)

# Menú de administrador
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 No tienes permisos para acceder a este menú.")
        return

    keyboard = [
        [InlineKeyboardButton("📤 Subir archivo", callback_data="upload_file")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("🛠 Menú de administrador:", reply_markup=reply_markup)

# Función para iniciar la subida de archivos
async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entrando a start_upload")  # Mensaje de depuración
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 No tienes permisos para acceder a esta función.")
        return ConversationHandler.END

    await update.callback_query.message.reply_text(
        "📤 Por favor, sube el archivo que deseas asociar a un código.",
        reply_markup=cancel_keyboard
    )
    return UPLOAD

# Manejar la subida de archivos
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entrando a handle_file_upload")  # Mensaje de depuración

    try:
        message = update.message
        file = None
        file_name = "archivo_sin_nombre"

        if message.document:
            file = message.document
            file_name = file.file_name or "archivo_sin_nombre"
        elif message.audio:
            file = message.audio
            file_name = file.file_name or "audio_sin_nombre.mp3"
        elif message.photo:
            file = message.photo[-1]  # Selecciona la foto con mayor resolución
            file_name = "imagen_sin_nombre.jpg"
        elif message.video:
            file = message.video
            file_name = "video_sin_nombre.mp4"
        elif message.voice:
            file = message.voice
            file_name = "nota_de_voz.ogg"
        elif message.sticker:
            file = message.sticker
            file_name = "sticker_sin_nombre.webp"

        if not file:
            await update.message.reply_text("❌ No se recibió un archivo válido. Por favor, intenta nuevamente.")
            return UPLOAD

        file_id = file.file_id
        print(f"Procesando archivo: file_id={file_id}, file_name={file_name}")  # Depuración

        add_file(file_name, file_id, "archivo")
        context.user_data['file_id'] = file_id
        print(f"context.user_data después de guardar file_id: {context.user_data}")  # Depuración

        await update.message.reply_text(f"✅ Archivo '{file_name}' guardado con éxito.")

        # Solicitar la cantidad de códigos
        await update.message.reply_text(
            "🔢 ¿Cuántos códigos deseas generar para este archivo?",
            reply_markup=cancel_keyboard
        )
        return ASK_CODE_QUANTITY

    except Exception as e:
        print(f"Error al procesar el archivo: {e}")  # Log del error
        await update.message.reply_text("❌ Ocurrió un error al procesar el archivo. Por favor, intenta nuevamente.")
        return UPLOAD


# Manejar la cantidad de códigos y generarlos
async def handle_code_quantity_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entrando a handle_code_quantity_and_generate")  # Mensaje de depuración
    print(f"context.user_data en handle_code_quantity_and_generate: {context.user_data}")  # Depuración

    # Verificar que update.message no sea None
    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Por favor, ingresa un número válido.")
        return ASK_CODE_QUANTITY

    try:
        # Obtener la cantidad ingresada por el usuario
        quantity = int(update.message.text.strip())
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
    except ValueError:
        await update.message.reply_text("❌ Por favor, ingresa un número válido mayor a 0.")
        return ASK_CODE_QUANTITY

    # Obtener el ID del archivo desde el contexto
    file_id = context.user_data.get('file_id')
    if not file_id:
        await update.message.reply_text("❌ Ocurrió un error al procesar el archivo. Por favor, intenta nuevamente.")
        return ConversationHandler.END

    # Generar los códigos y asociarlos al archivo
    codes = add_coupon(file_id, quantity)
    codes_text = "\n".join(codes)
    await update.message.reply_text(f"✅ Se generaron {quantity} códigos:\n{codes_text}")

    # Finalizar el flujo
    await update.message.reply_text("🎉 Proceso completado. ¿Necesitas algo más?", reply_markup=cancel_keyboard)
    return ConversationHandler.END

# Manejar el ingreso del código del cupón
async def handle_redeem_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().upper()
    user_id = update.effective_user.id

    # Validar el cupón
    file_ids = validate_coupon(user_input)

    if not file_ids:
        await update.message.reply_text("❌ Cupón inválido. Verifica el código e inténtalo de nuevo.")
        return REDEEM

    if coupon_used_by_user(user_id, user_input):
        await update.message.reply_text("🔁 Ya redimiste este cupón. Aquí están tus archivos:")
    else:
        register_redemption(user_id, user_input)
        await update.message.reply_text("✅ ¡Cupón válido! Aquí tienes tus archivos:")

    # Enviar los archivos asociados al cupón
    for file_id in file_ids:
        archivo = get_file_by_id(file_id)
        if archivo:
            name, telegram_file_id = archivo
            await update.message.reply_document(telegram_file_id, caption=f"🎵 {name}")

    return ConversationHandler.END

# Manejar el callback query "redeem"
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'redeem':
        await query.message.reply_text("🔑 Ingresa el código de cupón:", reply_markup=cancel_keyboard)
        return REDEEM

# Iniciar la aplicación
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_upload, pattern="^upload_file$")],
        states={
            UPLOAD: [MessageHandler(filters.ATTACHMENT, handle_file_upload)],
            ASK_CODE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_quantity_and_generate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("admin", admin_menu))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == '__main__':
    main()