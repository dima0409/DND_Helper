import aiosqlite

async def create_session(user_id: int, session: str):
    async with aiosqlite.connect('db/database.db') as db:
        await db.execute("INSERT INTO users (user_id, session, role) VALUES (?, ?, ?)", (user_id, session, 'master'))
        await db.commit()

async def join_session(user_id: int, session: str):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT * FROM users WHERE session = ?", (session,)) as cursor:
            session_exists = await cursor.fetchone()
        role = 'player' if session_exists else 'master'
        await db.execute("INSERT INTO users (user_id, session, role) VALUES (?, ?, ?)", (user_id, session, role))
        await db.commit()
        return role

async def get_role(user_id: int):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            role = await cursor.fetchone()
        return role[0] if role else None

async def delete_session(session: str):
    async with aiosqlite.connect('db/database.db') as db:
        await db.execute("DELETE FROM users WHERE session = ?", (session,))
        await db.commit()

async def get_sessions():
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT DISTINCT session FROM users") as cursor:
            sessions = await cursor.fetchall()
        return [session[0] for session in sessions]

async def get_master_session(user_id: int):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT session FROM users WHERE user_id = ? AND role = 'master'", (user_id,)) as cursor:
            session = await cursor.fetchone()
        return session[0] if session else None

async def get_session_by_user(user_id: int):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT session FROM users WHERE user_id = ?", (user_id,)) as cursor:
            session = await cursor.fetchone()
        return session[0] if session else None

async def leave_session(user_id: int):
    async with aiosqlite.connect('db/database.db') as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()

async def user_has_session(user_id: int):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT 1 FROM users WHERE user_id = ? AND role = 'master'", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def get_users_in_session(session: str):
    async with aiosqlite.connect('db/database.db') as db:
        async with db.execute("SELECT user_id FROM users WHERE session = ?", (session,)) as cursor:
            users = await cursor.fetchall()
        return [user[0] for user in users]