import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import CATEGORIES, STRINGS
from database import redis_client, update_score, reset_user_score
from quiz_service import get_questions


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command is issued."""
    user_id = update.effective_user.id
    await redis_client.delete(f"lang:{user_id}")
    lang = await redis_client.get(f"lang:{user_id}")
    if not lang:
        keyboard = [
            [InlineKeyboardButton("🇮🇹 Italiano", callback_data="setlang_it"),
             InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en")]
        ]
        text = "🌍 Choose your language / Scegli la tua lingua:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            if update.message:
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")


async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    # take the pool from the db
    db_pool = context.application.bot_data["db_pool"]

    try:
        await reset_user_score(db_pool, user_id)

        #delelte in Redis
        await redis_client.delete(f"quiz_state:{user_id}")
        await redis_client.delete(f"last_category:{user_id}")


    except Exception as e:
        await update.message.reply_text("Error.")

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):

    s = STRINGS.get(lang)
    row = []
    keyboard = []
    for name, cat_id in CATEGORIES.items():
        display_name = name
        if lang == "en":
            translation = {"Storia": "History", "Scienze": "Science", "Informatica": "IT", "Arte": "Art",
                           "Cinema": "Movies", "Sport": "Sport"}
            display_name = translation.get(name, name)

        row.append(InlineKeyboardButton(display_name, callback_data=f"topic_{cat_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton(s["language"], callback_data="change_lang")])

    text = s["Welcome"]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Button management
async def button_handler (update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or "User"

    # language setting
    language = await redis_client.get(f"lang:{user_id}") or "it"
    s = STRINGS[language]

    # change language
    if data.startswith("setlang_"):
        new_lang = data.split("_")[1]
        await redis_client.set(f"lang:{user_id}", new_lang)
        await show_categories(update, context, new_lang)
        return

    # user choose a subject
    if data.startswith("topic_") or data == "retry":
        if data == "retry":
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except:
                pass

        if data.startswith("topic_"):
            cat_id = data.split("_")[1]

            await redis_client.set(f"last_category:{user_id}", cat_id, ex=3600)
            await query.edit_message_text(s["searching"])

        else:
            cat_id = await redis_client.get(f"last_category:{user_id}")
            if not cat_id:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(s["menu"], callback_data="back_menu")]])
                await context.bot.send_message(chat_id = update.effective_chat.id, text = s["expired"], reply_markup=keyboard)
                return

        #download the question
        quiz = await get_questions(cat_id, language)
        if not quiz:
            await context.bot.send_message(chat_id = update.effective_chat.id, text =s["noquestion"])
            return

        # save in redis the correct answerer
        quiz_data = {
            "correct_index": quiz["correct_index"],
            "options": quiz["options"]
        }
        await redis_client.set(f"quiz_state:{user_id}", json.dumps(quiz_data), ex=60)

        # button for answer
        options_button = []
        for idx, option_text in enumerate(quiz['options']):
            options_button.append([InlineKeyboardButton(option_text, callback_data=f"ans_{idx}")])

        options_button.append([InlineKeyboardButton(s["menu"], callback_data="back_menu")])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❓ *{quiz['text']}*",
            reply_markup=InlineKeyboardMarkup(options_button),
            parse_mode='Markdown'
        )

    # the user gave an answer
    elif data.startswith("ans_"):
        given_idx = int(data.split("_")[1])
        raw_data = await redis_client.get(f"quiz_state:{user_id}")

        if raw_data is None:
            await context.bot.send_message(chat_id = update.effective_chat.id, text ="⚠️ "+s["expired"])
            return

        quiz_data = json.loads(raw_data)
        options = quiz_data['options']
        correct_index = quiz_data["correct_index"]

        is_correct = (correct_index == given_idx)
        point = 1 if is_correct else 0
        db_pool = context.application.bot_data["db_pool"]
        total_score = await update_score(db_pool, user_id, username, point=point)

        correct_text = options[correct_index]

        msg = ""
        # check
        if is_correct:
            msg = f"\n\n{s['correct']}\n👉 *{correct_text}*"
        else:
            msg = f"\n\n{s['incorrect']}\n👉 *{correct_text}*"


        final_message = (
            f"{msg}\n\n"
            f"👤 User: *{username}*\n"
            f"🏆 Total Score: *{total_score}* punti\n"
        )

        # final buton
        retry_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(s["next"], callback_data="retry")],

            [InlineKeyboardButton(s["menu"], callback_data="back_menu")]
        ])


        # Delete the previous button
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass

        await context.bot.send_message(chat_id = update.effective_chat.id, text = final_message, reply_markup=retry_button, parse_mode='Markdown')

    # back to menu
    elif data == "back_menu":
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await start_command(update, context)