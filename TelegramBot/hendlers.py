from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import CATEGORIES
from database import redis_client, update_score
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

    text = "Welcome in the QuizBot! Choose a subject and start your play!"
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Button management
async def button_handler (update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or "Utente"
    # user choose a subject
    if data.startswith("topic_") or data == "retry":
        if data.startswith("topic_"):
            cat_id = data.split("_")[1]

            await query.edit_message_text("Search for a difficult question...")
        else:
            cat_id = await redis_client.hget(f"last category {user_id}")
            if not cat_id:
                await query.edit_message_text("NI don't remember the previus topi, go back to the menu")
                return

            await query.edit_message_text("🔄 Creating new questions...")
        #download the question
        quiz = await get_questions(cat_id)
        if not quiz:
            await query.edit_message_text("Sorry, I couldn't find that question.")
            return

        # save in redis the correct answerer
        await redis_client.set(f"quiz_state:{user_id}", quiz['correct_index'], ex=60)

        # button for answer
        options_button = []
        for idx, option_text in enumerate(quiz['options']):
            options_button.append([InlineKeyboardButton(option_text, callback_data=f"ans_{idx}")])

        options_button.append([InlineKeyboardButton("Back to Menu", callback_data="back_menu")])

        await query.edit_message_text(
            text=f"❓ *Question:*\n{quiz['text']}",
            reply_markup=InlineKeyboardMarkup(options_button),
            parse_mode='Markdown'
        )

    # the user gave an answer
    elif data.startswith("ans_"):
        given_idx = int(data.split("_")[1])
        correct_index = await redis_client.get(f"quiz_state:{user_id}")
        if correct_index is None:
            await query.edit_message_text("⚠️ Retry.")
            return
        is_correct = (int(correct_index) == given_idx)
        point = 1 if is_correct else 0
        db_pool = context.application.bot_data["db_pool"]
        total_score = await update_score(db_pool, user_id, username, point=point)

        # check
        if is_correct:
            msg = "Correct answer, you get a point!"
            # update score
            db_pool = context.application.bot_data["db_pool"]
            total_score = await update_score(db_pool, user_id, username, point = 1)
        else:
            msg = "Incorrect answer, you don't get a point!"

        final_message = (
            f"{msg}\n\n"
            f"👤 Utente: *{username}*\n"
            f"🏆 Punteggio totale: *{total_score}* punti\n"
            f"🎮 Partite giocate: (aggiornato)"
        )

        # final buton
        retry_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Next Question", callback_data="retry")],
            # Per ora puntiamo a back_menu per fargli scegliere
            [InlineKeyboardButton("Back to Menu", callback_data="back_menu")]
        ])


        await query.edit_message_text(text=final_message, reply_markup=retry_button, parse_mode="Markdown")

    # back to menu
    elif data == "back_menu":
        await start_command(update, context)