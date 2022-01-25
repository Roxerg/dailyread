import asyncpg
import asyncio
import bcrypt

import string
import random

import os
DB_URI = os.environ['DATABASE_URL']
USERNAME = os.environ['READSTATS_USER']
PASSWORD = os.environ['READSTATS_PASS']

async def get_connection():
    return await asyncpg.connect(dsn=DB_URI)        

async def init_db():

    

    conn = await get_connection()

    await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR NOT NULL UNIQUE,
            passwordHash VARCHAR NOT NULL
        );
        '''
    )

    await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS sessions(
            user_id INT,
            token VARCHAR,
            timestamp TIMESTAMP,
            PRIMARY KEY (user_id, token)
        )
        '''
    )

    await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS history(
            day DATE DEFAULT CURRENT_DATE,
            streak INT,
            user_id INT REFERENCES users (id),
            PRIMARY KEY (day, user_id)
        );
        '''
    ) 

    username = USERNAME

    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(str.encode(PASSWORD), salt)

    
    await conn.execute("INSERT INTO users (username, passwordHash) VALUES ($1, $2) ON CONFLICT DO NOTHING;", username, passwordHash.decode())
    await conn.close()


async def mark_today(username):
    conn = await get_connection()

    streak = 0
    user_id = None
    streak_res = await conn.fetch("SELECT streak, user_id FROM history JOIN users ON user_id=id WHERE username=$1 AND day=CURRENT_DATE-1;", username)
    
    if len(streak_res) > 0:
        streak = streak_res[0]['streak']
        user_id = streak_res[0]['user_id']
    else:
        user_res = await conn.fetch("SELECT id FROM users WHERE username=$1", username)
        user_id = user_res[0]['id']

    await conn.execute("INSERT INTO history (day, streak, user_id) VALUES (CURRENT_DATE, $1, $2)", streak+1, user_id)
    await conn.close()

    return True
    
async def get_today(username):
    conn = await get_connection()

    res = await conn.fetch("SELECT streak FROM history JOIN users ON user_id=id WHERE username=$1 AND day=CURRENT_DATE", username)
    if len(res) > 0:
        return res[0]['streak']
    else: 
        return 0


async def verify_login(username, password):
    conn = await get_connection()
    res = await conn.fetch("SELECT * FROM users WHERE username=$1", username)
    if len(res) == 0:
        return False
    user = res[0]
    passwordHash = str.encode(user['passwordhash'])

    # ok fine i'll do the bloody token. but lazily.

    if not bcrypt.checkpw(str.encode(password), passwordHash):
        await conn.close()
        return None
    
    token = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))

    await write_token(conn, user["id"], token)

    await conn.close()
    return token

async def clean_tokens(conn):
    await conn.execute('DELETE FROM sessions WHERE CURRENT_DATE - timestamp::date > 30;')

async def write_token(conn, user_id, token):
    await clean_tokens(conn)
    await conn.execute('INSERT INTO sessions (user_id, token, timestamp) VALUES ($1, $2, NOW())', user_id, token)

async def verify_token(token):

    conn = await get_connection()
    
    await clean_tokens(conn)
    res = await conn.fetch('SELECT username, user_id FROM sessions JOIN users ON user_id=id WHERE token=$1')
    await conn.close()
    if len(res) > 0:
        return {
            "username" : res["username"],
            "user_id" : res["user_id"]
        }
    else:
        return None

async def register(username, password):

    conn = await get_connection()

    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(str.encode(password), salt)

    status = await conn.execute("INSERT INTO users (username, passwordHash) VALUES ($1, $2) ON CONFLICT DO NOTHING;", username, passwordHash.decode())
    await conn.close()

    return status

async def leaderboard(limit):

    conn = await get_connection()

    res = await conn.fetch("SELECT username, MAX(streak) as topstreak FROM users JOIN history ON user_id=id GROUP BY username ORDER BY topstreak DESC LIMIT $1", limit)

    res = [{"rank": i+1, "user" : x['username'], "streak": x['topstreak']} for i,x in enumerate(res)]
    await conn.close()
    return res

async def userhistory(username):

    conn = await get_connection()
    res = await conn.fetch("SELECT * FROM history JOIN users ON user_id=id WHERE username=$1", username)
    return res




asyncio.run(init_db())