import bcrypt

import string
import random

from datetime import datetime


import psycopg2
import utils

import os
DB_URI = os.environ['DATABASE_URL']
USERNAME = os.environ['READSTATS_USER']
PASSWORD = os.environ['READSTATS_PASS']

conn = None

def get_connection():
    global conn
    if conn.closed != 0:
        print("REINITIALIZED DB >:(")
        conn = init_connection()
        return conn
    else:
        return conn    

def init_connection():
    return psycopg2.connect(dsn=DB_URI)     

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR NOT NULL UNIQUE,
            passwordHash VARCHAR NOT NULL
        );
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS sessions(
            user_id INT,
            token VARCHAR,
            timestamp TIMESTAMP,
            PRIMARY KEY (user_id, token)
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS history(
            day DATE DEFAULT CURRENT_DATE,
            streak INT,
            user_id INT REFERENCES users (id),
            note VARCHAR,
            page INT,
            book_id INT,
            PRIMARY KEY (day, user_id)
        );
        '''
    ) 
    
    # cur.execute("DROP TABLE user_books")
    # cur.execute("DROP TABLE books")
    # cur.execute("DROP TABLE authors")
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS authors(
            id SERIAL,
            name VARCHAR UNIQUE,
            PRIMARY KEY (id)
        );
    ''')

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS books(
            id SERIAL,
            author_id INT REFERENCES authors (id),
            title VARCHAR NOT NULL, 
            pages VARCHAR,
            isbn VARCHAR(20),
            PRIMARY KEY (id)
        );
        '''
    ) 

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS user_books (
            book_id INT REFERENCES books (id),
            user_id INT REFERENCES users (id),
            page INT,
            finished BOOLEAN,
            PRIMARY KEY (book_id, user_id)
        );
        '''
    ) 

    cur.execute('''
        ALTER TABLE history ADD COLUMN IF NOT EXISTS note VARCHAR
    ''')

    cur.execute('''
        ALTER TABLE history ADD COLUMN IF NOT EXISTS book_id INT
    ''')

    cur.execute('''
        ALTER TABLE history ADD COLUMN IF NOT EXISTS page INT
    ''')

    username = USERNAME

    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(str.encode(PASSWORD), salt)

    
    cur.execute("INSERT INTO users (username, passwordHash) VALUES (%s, %s) ON CONFLICT DO NOTHING;", [username, passwordHash.decode()] )
    
    conn.commit()

    cur.close()
    

def add_author_if_new(cur, author_name):

    author_name = utils.process_author(author_name)

    cur.execute("INSERT INTO authors (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id", [author_name])
    res = cur.fetchone()

    return res[0]

def add_book_if_new(cur, book_title, author_id=None):

    book_title = utils.process_title(title)

    if author_id:
        cur.execute("INSERT INTO books (title, author_id) VALUES (%s, %s) ON CONFLICT (title) DO UPDATE SET title=EXCLUDED.title, author_id=EXCLUDED.author_id RETURNING id", [book_title, author_id]) 
    else:
        cur.execute("INSERT INTO books (title) VALUES (%s) ON CONFLICT (title) DO UPDATE SET title=EXCLUDED.title RETURNING id", [book_title]) 
    res = cur.fetchone()

    return res[0]





def mark_today(username, advanced_data=None):
    conn = get_connection()
    cur = conn.cursor()

    streak = 0
    user_id = None
    
    cur.execute("SELECT streak, user_id FROM history JOIN users ON user_id=id WHERE username=%s AND day=CURRENT_DATE-1;", [username])
    streak_res = cur.fetchone()

    if streak_res != None:
        streak = streak_res[0]
        user_id = streak_res[1]
    else:
        cur.execute("SELECT id FROM users WHERE username=%s", [username])
        user_res = cur.fetchone()
        user_id = user_res[0]

    note, author, title = None, None, None
    if advanced_data:
        note = advanced_data.get("notes")
        author = advanced_data.get("author")
        title = advanced_data.get("title")

    author_id, book_id = None, None

    # create / get if specified
    if author:
        author_id = add_author_if_new(cur, author)

    if title:
        book_id = add_book_if_new(cur, book_title, author_id)

    # add relation 
    if book_id:
        cur.execute("INSERT INTO user_books (user_id, book_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", [user_id, book_id])
    
    cur.execute("INSERT INTO history (day, streak, user_id, note, book_id) VALUES (CURRENT_DATE, %s, %s, %s, %s) ON CONFLICT (day, user_id) DO UPDATE SET note = excluded.note", [streak+1, user_id, note, book_id])
    conn.commit()

    cur.execute("SELECT streak, user_id, note FROM history JOIN users ON user_id=id WHERE username=%s AND day=CURRENT_DATE-1;", [username])
    streak_res = cur.fetchone()

    cur.close()
    

    if streak_res != None:
        print(streak_res[2])
        if (streak_res[0] == streak):
            return False

    return True
    
def get_today(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT streak, day, note, day=CURRENT_DATE as current_day  FROM history JOIN users ON user_id=id WHERE username=%s AND day >= CURRENT_DATE - INTEGER '1' ORDER BY day DESC", [username])
    res = cur.fetchone()

    cur.close()

    print(res)
    

    if res != None:
        return {
            "streak": res[0],
            "today" : datetime.today().strftime('%Y-%m-%d') == res[1].strftime('%Y-%m-%d'),
            "note" : res[2] if res[3] else None,
        }
    else: 
        return None

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, username, passwordHash FROM users WHERE id=%s LIMIT 1", [user_id])
    res = cur.fetchone()

    if res != None:
        return res
    else:
        return None

def get_token_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT token, user_id FROM sessions WHERE user_id=%s", [user_id])
    res = cur.fetchone()

    if res != None:
        return res[0]
    else:
        return None


def verify_login(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT passwordHash, id FROM users WHERE username=%s", [username])
    res = cur.fetchone()

    if res == None:
        return False
    user = res

    passwordHash = str.encode(user[0])

    # ok fine i'll do the bloody token. but lazily.

    if not bcrypt.checkpw(str.encode(password), passwordHash):
        
        return None
    
    token = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))

    write_token(conn, cur, user[1], token)

    cur.close()
    
    return token

def verify_login_returning_data(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT passwordHash, id FROM users WHERE username=%s", [username])
    res = cur.fetchone()

    if res == None:
        return False
    user = res

    passwordHash = str.encode(user[0])

    # ok fine i'll do the bloody token. but lazily.

    if not bcrypt.checkpw(str.encode(password), passwordHash):
        cur.close()
        
        return None
    
    token = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))

    write_token(conn, cur, user[1], token)

    cur.close()
    

    return {
        "passwordhash" : user[0],
        "id" : user[1],
        "token" : token,
        "username" : username,
    }


def clean_tokens(conn, cur):
    cur.execute('DELETE FROM sessions WHERE CURRENT_DATE - timestamp::date > 30;')
    conn.commit()

def write_token(conn, cur, user_id, token):
    cur.execute('INSERT INTO sessions (user_id, token, timestamp) VALUES (%s, %s, NOW())', [user_id, token])
    clean_tokens(conn, cur)

def verify_token(token):

    conn = get_connection()
    cur = conn.cursor()
    
    clean_tokens(conn, cur)

    cur.execute('SELECT username, user_id FROM sessions JOIN users ON user_id=id WHERE token=%s', [token])
    res = cur.fetchone()

    cur.close()
    

    if res != None:
        return {
            "username" : res[0],
            "user_id" : res[1],
        }
    else:
        return None

def logout(user, token):

    conn = get_connection()
    cur = conn.cursor()


    clean_tokens(conn, cur)

    cur.execute("DELETE FROM sessions S USING users U WHERE S.user_id=U.id AND U.username=%s AND S.token=%s", [user, token])
    conn.commit()

    cur.close()
    

def register(username, password):

    conn = get_connection()
    cur = conn.cursor()

    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(str.encode(password), salt)

    status = cur.execute("INSERT INTO users (username, passwordHash) VALUES (%s, %s) ON CONFLICT DO NOTHING;", [username, passwordHash.decode()])

    conn.commit()
    cur.close()
    

    return True

def leaderboard_overall(limit):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, MAX(streak) as topstreak FROM users JOIN history ON user_id=id GROUP BY username ORDER BY topstreak DESC LIMIT %s", [limit])
    res = cur.fetchall()

    res = [{"rank": i+1, "user" : x[0], "streak": x[1]} for i,x in enumerate(res)]
    
    cur.close()
    
    return res

def leaderboard_ongoing(limit):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, MAX(streak) as topstreak FROM users JOIN history ON user_id=id WHERE day >= CURRENT_DATE - INTEGER '1' GROUP BY username ORDER BY topstreak DESC LIMIT %s", [limit])
    res = cur.fetchall()

    res = [{"rank": i+1, "user" : x[0], "streak": x[1]} for i,x in enumerate(res)]
    
    cur.close()
    
    return res

def userhistory(username):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT streak, day FROM history JOIN users ON user_id=id WHERE username=%s ORDER BY day DESC", [username])
    res = cur.fetchall()

    cur.close()
    
    return res



conn = init_connection()
init_db()