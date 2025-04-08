from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from db_functions import validate_coupon, coupon_used_by_user, register_redemption, get_file_by_id, add_coupon, add_file, init_db
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext,
    CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
)

import sqlite3

init_db()
UPLOAD, CREATE_COUPON, ASSIGN_FILE = range(3)
ASSIGN_COUPON, SELECT_FILE = range(3, 5)

ADMIN_IDS = [851194595]

DB = "bot_store.db"

TOKEN = '7987679597:AAHK4k-8kzUmDBfC9_R1cVroDqXEDqz6sB4'

# Estados de conversación
REDEEM = 1

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
        await update.callback_query.message.reply_text(
            "🔑 Ingresa el código de cupón:",
            reply_markup=cancel_keyboard
        )
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
    keyboard = [
        [InlineKeyboardButton("🧾 Redimir cupón", callback_data='redeem')],
        [InlineKeyboardButton("🎵 Mis archivos", callback_data='my_files')],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("❌ Operación cancelada.", reply_markup=reply_markup)
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
        [InlineKeyboardButton("🔗 Asociar archivo a cupón", callback_data='assign_file')],  # nuevo botón
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Menú de administrador:", reply_markup=reply_markup)
    
from db_functions import add_file  # Función que ahora veremos

# Estados

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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
        await query.message.reply_text("✍️ Escribe el código del cupón al que deseas asociar un archivo:")
        return ASSIGN_COUPON

    return ConversationHandler.END

async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass  # Si ya pasó el tiempo, simplemente ignóralo
    
    await query.message.reply_text("📤 Envía el archivo de audio (WAV o MP3):")
    return UPLOAD

async def start_create_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 Escribe el código del nuevo cupón (formato XXX-XXX):")
    return CREATE_COUPON


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = None
    name = "audio_sin_nombre.mp3"
    mime_type = ""

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

    if not mime_type.startswith("audio/"):
        # A veces los reenvíos no tienen MIME, así que damos una advertencia en vez de bloquear
        await update.message.reply_text("⚠️ Archivo sin tipo MIME. Lo guardaré de todas formas.")
    
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

async def receive_coupon_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    context.user_data['coupon_to_assign'] = code

    # Aquí puedes listar archivos disponibles si quieres
    await update.message.reply_text("📎 Ahora reenvíame el archivo que deseas asociar a este cupón.")
    return SELECT_FILE

from db_functions import associate_file_with_coupon  # esta función la hacemos en un momento

async def assign_file_to_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None
    if update.message.document:
        file = update.message.document
    elif update.message.audio:
        file = update.message.audio
    
    if not file:
        await update.message.reply_text("❌ No se detectó un archivo válido.")
        return ConversationHandler.END

    coupon = context.user_data.get('coupon_to_assign')
    if not coupon:
        await update.message.reply_text("⚠️ No se encontró el cupón en contexto.")
        return ConversationHandler.END

    file_id = file.file_id
    name = file.file_name or "sin_nombre"
    
    # Aquí buscamos el ID real en base de datos por file_id
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM files WHERE telegram_file_id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("⚠️ El archivo no está registrado aún. Súbelo primero.")
        return ConversationHandler.END

    file_db_id = row[0]
    associate_file_with_coupon(coupon, file_db_id)

    await update.message.reply_text(f"✅ Archivo asociado exitosamente al cupón {coupon}.")
    return ConversationHandler.END

async def show_redeemed_files(update, context, order_by="recent", page=0):
    user_id = update.effective_user.id
    limit = 5
    offset = page * limit

    files, total = get_redeemed_files_by_user(user_id, order_by, limit, offset)
    total_pages = (total + limit - 1) // limit

    if not files:
        await update.message.reply_text("No has redimido ningún archivo todavía.")
        return

    text = f"📦 Archivos redimidos ({total} total):\n\n"
    for name, file_id, timestamp in files:
        text += f"• {name} (📥 ID: `{file_id}`)\n  └ 📅 Redimido: {timestamp}\n\n"

    # Botones
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Anterior", callback_data=f"view_{order_by}_{page-1}") if page > 0 else InlineKeyboardButton(" ", callback_data="noop"),
            InlineKeyboardButton("➡️ Siguiente", callback_data=f"view_{order_by}_{page+1}") if (offset + limit) < total else InlineKeyboardButton(" ", callback_data="noop"),
        ],
        [
            InlineKeyboardButton("🔄 Recientes", callback_data="view_recent_0"),
            InlineKeyboardButton("🔤 Por nombre", callback_data="view_name_0"),
        ]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_view_files_callback(update, context):
    query = update.callback_query
    await query.answer()  # Importante para evitar el "relojito" de Telegram

    data = query.data
    if data.startswith("view_"):
        try:
            _, order_by, page = data.split("_")
            page = int(page)
            await show_redeemed_files(update, context, order_by=order_by, page=page)
        except Exception as e:
            await query.edit_message_text("⚠️ Error procesando tu solicitud.")

async def command_mis_archivos(update, context):
    await show_redeemed_files(update, context, order_by="recent", page=0)

app.add_handler(CommandHandler("mis_archivos", command_mis_archivos))

# Iniciar la aplicación
def main():
    app = ApplicationBuilder().token(TOKEN).build()


    admin_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_upload, pattern="^upload_file$"),
        CallbackQueryHandler(start_create_coupon, pattern="^create_coupon$"),
        CallbackQueryHandler(admin_button_handler, pattern="^assign_file$"),
    ],
    states={
        UPLOAD: [MessageHandler(filters.ATTACHMENT, handle_file_upload)],
        SELECT_FILE: [MessageHandler(filters.ATTACHMENT, assign_file_to_coupon)],

        CREATE_COUPON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_coupon)],
        ASSIGN_COUPON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coupon_code)],

    },
    fallbacks=[CommandHandler("cancel", cancel)],
    )
    # Conversación para redimir cupón
    redeem_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="^(redeem|my_files|help)$")],
    states={
        REDEEM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^❌ Cancelar$"), redeem_coupon),
            MessageHandler(filters.Regex("^❌ Cancelar$"), cancel)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
    allow_reentry=True,
    )


    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(redeem_conv)
    app.add_handler(CommandHandler("admin", admin_menu))
    app.add_handler(CallbackQueryHandler(handle_view_files_callback, pattern=r"^view_"))
    application.add_handler(CommandHandler("mis_archivos", command_mis_archivos))


    print("🤖 Bot corriendo...")
    
    app.run_polling()

if __name__ == '__main__':
    main()


