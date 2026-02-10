CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,  -- unique user ID
    username TEXT,                   -- For the classification
    total_score INT DEFAULT 0,       -- Total score
    games_played INT DEFAULT 0,      -- Number of questions
    last_played TIMESTAMP            -- Inactive users
);