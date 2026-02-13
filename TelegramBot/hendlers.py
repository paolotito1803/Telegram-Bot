from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import CATEGORIES
from database import redis_client
from quiz_service import get_questions


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    """Send a message when the command is issued."""
    row = []
    keyboard = []
    for name, cat_id in CATEGORIES.items() :
        row.append(InlineKeyboardButton(name, callback_data=f"topic_{cat_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await update.message.reply_text(
        "Welcome in the QuizBot! Choose a subject and start your play!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Button management
async def buttn_handler (update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username

    # user choose a subject
    if data.startswith("topic_"):
        cat_id = data.split("_")[1]

        await query.edit_message_text("Search for a difficult question...")

        #download the question
        quiz = await get_questions(cat_id)
        if not quiz:
            await query.edit_message_text("Sorry, I couldn't find that question.")
            return

        # save in redis the correct answerer
        await redis_client.set(f"quiz_state:{user_id}", quiz['correct_index'], ex=60)