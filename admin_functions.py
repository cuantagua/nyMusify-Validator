from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
from telegram.ext import ContextTypes, ConversationHandler  # type: ignore
from db_functions import add_file, add_coupon, associate_file_with_coupon
import sqlite3
from config import DB, ADMIN_IDS
import random
import csv

UPLOAD, GENERATE_CODE, ASK_CODE_QUANTITY = range(3)  # Estados únicos

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

    if query.data == "generate_code":
        await query.message.reply_text("🧮 ¿Cuántos códigos deseas generar?")
        return ASK_CODE_QUANTITY

    elif query.data == "finish_upload":
        await query.message.reply_text("✅ Proceso finalizado. Gracias.")
        return ConversationHandler.END

async def handle_code_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cantidad = int(update.message.text.strip())
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")

        file_id = context.user_data.get('last_uploaded_file_id')
        if not file_id:
            await update.message.reply_text("❌ No se encontró el archivo para asociar los códigos.")
            return ConversationHandler.END

        # Generar los códigos
        codes = []
        for _ in range(cantidad):
            code = f"{random.randint(100, 999)}-{random.randint(100, 999)}"
            success = add_coupon(code)
            if success:
                associate_file_with_coupon(code, file_id)
                codes.append(code)

        # Guardar los códigos en un archivo CSV
        csv_file = "generated_codes.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Código"])
            writer.writerows([[code] for code in codes])

        # Enviar el archivo CSV al administrador
        with open(csv_file, "rb") as f:
            await update.message.reply_document(f, filename=csv_file, caption="✅ Aquí están los códigos generados.")

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Por favor, escribe un número válido.")
        return ASK_CODE_QUANTITY