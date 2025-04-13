from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, CommandHandler, filters  # type: ignore
from db_functions import add_file, add_coupon, associate_file_with_coupon
import sqlite3
from config import DB, ADMIN_IDS
import random
import csv

UPLOAD, GENERATE_CODE, ASK_CODE_QUANTITY = range(3)  # Estados únicos

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if (user_id not in ADMIN_IDS):
        await update.message.reply_text("🚫 No tienes permisos para acceder a este menú.")
        return

    keyboard = [[InlineKeyboardButton("📤 Subir archivo", callback_data='upload_file')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Menú de administrador:", reply_markup=reply_markup)

async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entrando a start_upload")  # Mensaje de depuración
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 No tienes permisos para acceder a esta función.")
        return ConversationHandler.END

    await update.callback_query.message.reply_text(
        "📤 Por favor, sube el archivo que deseas asociar a un código.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]])
    )
    return UPLOAD

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entrando a handle_file_upload")  # Mensaje de depuración

    # Verifica si el mensaje contiene un archivo como documento o audio
    doc = update.message.document if update.message else None
    audio = update.message.audio if update.message else None

    if not doc and not audio:
        await update.message.reply_text("❌ No se recibió un archivo válido. Por favor, intenta nuevamente.")
        return UPLOAD

    # Procesa el archivo como documento o audio
    file_id = doc.file_id if doc else audio.file_id
    file_name = doc.file_name if doc else (audio.file_name or "archivo_sin_nombre.mp3")

    # Guarda el archivo en el contexto del usuario
    context.user_data['last_uploaded_file_id'] = file_id
    context.user_data['last_uploaded_file_name'] = file_name
    print(f"Archivo guardado en context.user_data: {context.user_data}")  # Depuración

    # Guarda el archivo en la base de datos
    add_file(file_name, file_id, "archivo")

    # Mensaje de confirmación
    await update.message.reply_text(f"✅ Archivo '{file_name}' guardado con éxito.")

    # Ofrecer opciones al usuario
    keyboard = [
        [InlineKeyboardButton("✅ Generar códigos", callback_data="generate_code")],
        [InlineKeyboardButton("❌ Finalizar", callback_data="finish_upload")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "¿Qué deseas hacer ahora?",
        reply_markup=reply_markup
    )
    return GENERATE_CODE

async def handle_generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    print(f"context.user_data en handle_generate_code: {context.user_data}")  # Depuración

    if query.data == "generate_code":
        await query.message.reply_text("🧮 ¿Cuántos códigos deseas generar?")
        return ASK_CODE_QUANTITY

    elif query.data == "finish_upload":
        await query.message.reply_text("✅ Proceso finalizado. Gracias.")
        return ConversationHandler.END

async def handle_code_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"context.user_data en handle_code_quantity: {context.user_data}")  # Depuración

    try:
        cantidad = int(update.message.text.strip())
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")

        file_id = context.user_data.get('last_uploaded_file_id')
        file_name = context.user_data.get('last_uploaded_file_name')
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
        csv_file = f"codes_for_{file_name}.csv"
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

admin_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_upload, pattern="^upload_file$")],
    states={
        UPLOAD: [MessageHandler(filters.ATTACHMENT, handle_file_upload)],
        GENERATE_CODE: [CallbackQueryHandler(handle_generate_code, pattern="^(generate_code|finish_upload)$")],
        ASK_CODE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_quantity)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)