from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler,
    CallbackContext, filters
)

ADMIN_PANEL, WAITING_FILE, WAITING_TYPE, CONFIRM_COUPONS, ASK_COUPON_QTY = range(5)

# Lista de tipos disponibles
FILE_TYPES = ["música", "libro", "película"]

# Comando /admin
async def admin_panel(update: Update, context: CallbackContext):
    keyboard = [["Subir archivo"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Bienvenido al panel de administrador. Elige una opción:", reply_markup=reply_markup)
    return ADMIN_PANEL

# Recibe la opción
async def handle_admin_choice(update: Update, context: CallbackContext):
    if update.message.text == "Subir archivo":
        await update.message.reply_text("Por favor, envía el archivo que quieres subir.")
        return WAITING_FILE
    else:
        await update.message.reply_text("Opción no válida.")
        return ADMIN_PANEL
