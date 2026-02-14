import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from database import create_pool
from hendlers import start_command, button_handler

# logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()


def main():
    print("--- INIZIO MAIN ---")

    # 1. Definisci la funzione post_init PRIMA di costruire l'app
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
        return  # Esce dal programma se manca il token

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)  # <--- SI PASSA QUI!
        .build()
    )

    # 3. handlers registration
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # 4. start
    print("--- 🚀 AVVIO POLLING ---")
    application.run_polling()


if __name__ == "__main__":
    main()