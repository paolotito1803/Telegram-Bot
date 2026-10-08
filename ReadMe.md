# 🧠 Async Telegram Trivia Bot

A fully asynchronous, high-concurrency Telegram bot for trivia quizzes.

This project fetches questions from an external REST API, manages ephemeral user states via in-memory caching, and persists user scores in a relational database. The entire application is containerized using Docker for seamless deployment.

## 🚀 Features

* **Real-Time Trivia Generation:** Fetches questions dynamically from the [Open Trivia Database](https://opentdb.com/) via async HTTP requests.
* **On-the-fly Translation:** Automatically translates questions and answers into different languages (IT/EN) without blocking the main event loop.
* **High Concurrency:** Built entirely with Python's `asyncio` and `python-telegram-bot` (v20+) to handle multiple users simultaneously without blocking threads.
* **Volatile State Management:** Uses **Redis** to temporarily store the current quiz state (e.g., the correct answer index) with an auto-expiration TTL, ensuring zero latency and offloading the primary database.
* **Persistent Gamification:** Uses **PostgreSQL** to store user profiles, track total scores, and allow custom usernames.
* **Dockerized Architecture:** The application, cache, and database are orchestrated via **Docker Compose**, ensuring a clean and reproducible environment.

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Bot Framework:** `python-telegram-bot`
* **Database:** PostgreSQL (with `asyncpg` driver)
* **Cache:** Redis (with `redis.asyncio` driver)
* **API Requests:** `aiohttp`
* **Containerization:** Docker & Docker Compose

## 🏗 Architecture Overview

1. **User Request:** The user selects a category via Inline Keyboards.
2. **API Fetch:** The bot makes an async GET request to OpenTDB.
3. **State Caching:** The correct answer and the options are serialized (JSON) and cached in **Redis** with a 60-second TTL.
4. **User Response:** When the user clicks an answer, the bot validates it against the Redis cache.
5. **Persistence:** If the answer is correct, the bot updates the user's total score in **PostgreSQL**.

## ⚙️ Prerequisites

Before you begin, ensure you have met the following requirements:

* [Docker](https://www.docker.com/) and Docker Compose installed on your machine.
* A Telegram Bot Token (you can get one from [@BotFather](https://t.me/botfather) on Telegram).

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YourUsername/your-repo-name.git
cd your-repo-name
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and add the following configuration:

```ini
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=telegram_bot_db
DB_USER=bot_user
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

### 3. Run the Application

Build and start the containers in detached mode:

```bash
docker-compose up -d --build
```

### 4. Check Logs

To ensure everything is running smoothly:

```bash
docker-compose logs -f bot
```

## 🎮 Bot Commands

* `/start` - Initializes the bot, allows language selection, and opens the category menu.
* `/setname <name>` - Sets a custom username for the leaderboard and score tracking.
* `/leave` - Quits the current session and resets the user's score to zero.

## 📂 Project Structure

```text
├── Dockerfile             # Docker image configuration for the Python bot
├── docker-compose.yml     # Orchestrates Bot, PostgreSQL, and Redis containers
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (ignored in Git)
├── init.sql               # Database schema initialization
├── main.py                # Application entry point and setup
├── handlers.py            # Telegram commands and CallbackQuery logic
├── database.py            # Asyncpg and Redis connection pooling/queries
├── quiz_service.py        # External API fetching and data formatting
└── config.py              # Static configuration (categories, strings)
```
