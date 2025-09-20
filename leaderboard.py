import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import re
import json
import os
from keep_alive import keep_alive
keep_alive()

# your bot code below


# --- CONFIG ---
TOKEN = "8010377177:AAEBYNPOXTlJRA2hTFKMQ0cgvojKx85QrUI"
ADMINS = [7886650854, 7775458392, 8432963214]  # Replace with actual admin user IDs
DATA_FILE = "users.json"

# --- DATA STORAGE ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
        # Convert keys to int because JSON stores keys as strings
        users = {int(k): v for k, v in users.items()}
else:
    users = {}  # user_id: {"username": str, "points": int}


# --- HELPER TO SAVE DATA ---
def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)


# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users:
        users[user.id] = {"username": user.username or user.first_name, "points": 0}
        save_users()
        await update.message.reply_text("✅ You are registered in the leaderboard!")
    else:
        await update.message.reply_text("ℹ️ You are already registered.")


# --- POINT COMMAND ---
async def point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMINS:
        await update.message.reply_text("🚫 Only admins can add points.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /point <points> <username/userid>")
        return

    try:
        points = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Points must be an integer.")
        return

    target = context.args[1]

    # Find target user by id or username
    target_id = None
    if target.isdigit():
        target_id = int(target)
    else:
        for uid, data in users.items():
            if data["username"] and data["username"].lower() == target.lower().lstrip("@"):
                target_id = uid
                break

    if target_id is None or target_id not in users:
        await update.message.reply_text("❌ User not found or not registered.")
        return

    users[target_id]["points"] += points
    save_users()
    await update.message.reply_text(
        f"✅ Added {points} points to {users[target_id]['username']} (Total: {users[target_id]['points']})"
    )


# --- LEADERBOARD COMMAND ---
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_leaderboard(update, context, page=0)


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["points"], reverse=True)
    start_idx = page * 10
    end_idx = start_idx + 10
    leaderboard_slice = sorted_users[start_idx:end_idx]

    if not leaderboard_slice:
        if update.callback_query:
            await update.callback_query.answer("No more users.")
        return

    text = "🏆 Leaderboard 🏆\n\n"
    for rank, (uid, data) in enumerate(leaderboard_slice, start=start_idx + 1):
        text += f"{rank}. {data['username']} — {data['points']} pts\n"

    # Inline buttons
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"leaderboard_{page-1}"))
    if end_idx < len(sorted_users):
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"leaderboard_{page+1}"))

    reply_markup = InlineKeyboardMarkup([keyboard] if keyboard else [])

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


# --- CALLBACK HANDLER ---
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    match = re.match(r"leaderboard_(\d+)", query.data)
    if match:
        page = int(match.group(1))
        await show_leaderboard(update, context, page)


# --- MAIN ---
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("point", point))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"leaderboard_\d+"))

    app.run_polling()


if __name__ == "__main__":
    main()
