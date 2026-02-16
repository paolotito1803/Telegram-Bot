import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from database import create_pool
from hendlers import start_command, button_handler, leave_command

# logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()


def main():
    print("--- INIZIO MAIN ---")


    async def post_init(app):
        print("--- TENTO CONNESSIONE DB ---")
        try:
            pool = await create_pool()
            app.bot_data["db_pool"] = pool
            print("--- ✅ DB CONNESSO ---")
        except Exception as e:
            print(f"--- ❌ ERRORE DB: {e}")


    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ ERRORE: TELEGRAM_TOKEN non trovato!")
        return

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )


    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("leave", leave_command))
    application.add_handler(CallbackQueryHandler(button_handler))


    print("--- 🚀 AVVIO POLLING ---")
    application.run_polling()


if __name__ == "__main__":
    main()