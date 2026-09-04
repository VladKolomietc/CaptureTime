import aiosqlite
from datetime import datetime

DB_PATH = 'datab/capture_time.db'

async def create_database():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                tg_id INTEGER NOT NULL UNIQUE,
                user_name TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS capture (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                captured_at TEXT NOT NULL,
                focus_time INTEGER NOT NULL,
                music_title TEXT,
                author TEXT, 
                FOREIGN KEY (user_id) REFERENCES users (id) 
                    ON DELETE CASCADE 
                    ON UPDATE NO ACTION
            )
        """)
        
        await db.commit()

async def add_user(tg_id: int, user_name: str):
    async with aiosqlite.connect(DB_PATH) as db: 
        await db.execute("""
            INSERT OR IGNORE INTO users (tg_id, user_name)
            VALUES (?, ?);
        """, (tg_id, user_name))
        await db.commit()

    print(f"{user_name} with tg id {tg_id} was inserted")
    
async def add_capture(tg_id: int, captured_at: str, time_part: int, music_title: str, author: str):
    hours, minutes = map(int, time_part.split(":"))
    focus_time = hours * 60 + minutes

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO capture (user_id, captured_at, focus_time, music_title, author)
            VALUES ((SELECT id FROM users WHERE tg_id = ?), ?, ?, ?, ?);
        """, (tg_id, captured_at, focus_time, music_title, author))
        await db.commit()

    print(f"New capture is created for tg_id {tg_id}")

async def user_captures_list(tg_id: int) -> list[tuple[int, str, str | None, str | None]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, captured_at, focus_time, music_title, author 
            FROM capture 
            WHERE user_id = (SELECT id FROM users WHERE tg_id = ?)
            ORDER BY captured_at;
        """, (tg_id,)) as cursor:
            return await cursor.fetchall()

async def get_entry(tg_id: int, entry_number: int) -> list[tuple[int, str, str | None, str | None]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, captured_at, focus_time, music_title, author
            FROM capture
            WHERE user_id = (SELECT id FROM users WHERE tg_id = ?) and id = ?;
        """, (tg_id, entry_number)) as cursor:
            return await cursor.fetchall()

async def delete_entry(entry_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        DELETE FROM capture
        WHERE id = ?; 
    """, (entry_id,))
        await db.commit()

async def update_entry(entry_id, column_name: str, new_value):
    async with aiosqlite.connect(DB_PATH) as db: 
        query = f"""
            UPDATE capture
            SET {column_name} = ?
            WHERE id = ?;
        """
        await db.execute(query, (new_value, entry_id))
        await db.commit()