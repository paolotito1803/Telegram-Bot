import os

import redis.asyncio as redis
from dotenv import load_dotenv
import asyncpg

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

async def create_pool(): # Connection to the DB
    return await asyncpg.create_pool(
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"),
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT")
    )

async def update_score(pool, user_id, username, point = 1):
    async with pool.acquire() as conn:
        new_score = await conn.fetchval("""
                                        INSERT INTO users(telegram_id, username, total_score, games_played, last_played)
                                        VALUES ($1, $2, $3, 1, NOW()) ON CONFLICT (telegram_id) DO
                                        UPDATE
                                            SET total_score = users.total_score + EXCLUDED.total_score,
                                            games_played = users.games_played + 1,
                                            last_played = NOW(),
                                            username = $2
                                            RETURNING total_score
                                        """, user_id, username, point)
        return new_score

# Ranking
async def get_top_userss(pool, limit = 10):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT username, total_score, games_played FROM users ORDER BY total_score DESC LIMIT $1
        """, limit)
    return rows

