import aiosqlite

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
                music_title TEXT,
                author TEXT, 
                FOREIGN KEY (user_id) REFERENCES users (id) 
                    ON DELETE CASCADE 
                    ON UPDATE NO ACTION
            )
        """)
        
        await db.commit()