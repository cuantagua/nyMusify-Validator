from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
from telegram.ext import ContextTypes, ConversationHandler # type: ignore
from db_functions import add_file, add_coupon, associate_file_with_coupon
import sqlite3
from config import DB, ADMIN_IDS

GENERATE_CODE = 1  # Define el valor correcto según tu flujo de estados
GENERATE_CODE = range(1)  # Nuevo estado para generar código

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 No tienes permisos para acceder a este menú.")
        return

    keyboard = [[InlineKeyboardButton("📤 Subir archivo", callback_data='upload_file')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Menú de administrador:", reply_markup=reply_markup)

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = None
    name = "audio_sin_nombre.mp3"
    mime_type = ""
    tipo = "musica"

    if update.message.document:
        doc = update.message.document
        name = doc.file_name or "audio_documento.mp3"
        mime_type = doc.mime_type or ""
    elif update.message.audio:
        doc = update.message.audio
        name = doc.file_name or doc.title or "audio.mp3"
        mime_type = doc.mime_type or ""

    if not doc:
        await update.message.reply_text("❌ No se recibió un archivo válido.")
        return ConversationHandler.END

    file_id = doc.file_id
    add_file(name, file_id, tipo)

    # Guardar el ID del archivo en el contexto para usarlo más adelante
    context.user_data['last_uploaded_file_id'] = file_id
    context.user_data['last_uploaded_file_name'] = name

    # Preguntar si desea generar un código
    keyboard = [
        [InlineKeyboardButton("✅ Sí, generar códigos", callback_data="generate_code")],
        [InlineKeyboardButton("❌ No, finalizar", callback_data="finish_upload")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Archivo '{name}' guardado con éxito.\n\n¿Deseas generar un código para este archivo?",
        reply_markup=reply_markup
    )
    return GENERATE_CODE

async def handle_generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("📋 Entraste en la función para generar códigos.")

    if query.data == "generate_code":
        await query.message.reply_text("🧮 ¿Cuántos códigos deseas generar?")
        return ASK_CODE_QUANTITY

    elif query.data == "finish_upload":
        await query.message.reply_text("✅ Proceso finalizado.")
        return ConversationHandler.END