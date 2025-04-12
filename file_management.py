from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db_functions import get_redeemed_files_by_user

async def show_redeemed_files(update: Update, context: ContextTypes.DEFAULT_TYPE, order_by="recent", page=0):
    user_id = update.effective_user.id
    limit = 5
    offset = page * limit

    files, total = get_redeemed_files_by_user(user_id, order_by, limit, offset)
    total_pages = (total + limit - 1) // limit

    message = update.message or update.callback_query.message

    if not files:
        await message.reply_text("No has redimido ningún archivo todavía.")
        return

    keyboard = []

    for index, (name, file_id, _) in enumerate(files):
        short_id = f"{page}_{index}"
        context.user_data[f"file_{short_id}"] = file_id

        keyboard.append([
            InlineKeyboardButton(f"📥 {name}", callback_data=f"getfile_{short_id}")
        ])

    navigation = [
        InlineKeyboardButton("⬅️ Anterior", callback_data=f"view_{order_by}_{page-1}") if page > 0 else InlineKeyboardButton(" ", callback_data="noop"),
        InlineKeyboardButton("➡️ Siguiente", callback_data=f"view_{order_by}_{page+1}") if (offset + limit) < total else InlineKeyboardButton(" ", callback_data="noop"),
    ]
    keyboard.append(navigation)

    await message.reply_text(
        "📦 Archivos redimidos:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )