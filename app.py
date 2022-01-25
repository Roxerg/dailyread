from flask import Flask
from flask import request

from flask_cors import CORS

import db_client

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
async def ping():
    return "pong"

@app.route("/mark", methods=['GET', 'POST'])
async def mark_today_read():
    if request.json == None:
        return "body must contain login (user, pass)"

    if not 'user' in request.json or not 'pass' in request.json:
        return "body must contain login (user, pass)"

    username = request.json['user']
    password = request.json['pass']

    valid = await db_client.verify_login(username, password)
    if valid:
        if await db_client.mark_today(username):
            return "marked today"
    return "failed"

@app.route("/mark-with-token", methods=['GET', 'POST'])
async def mark_today_read_token():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return "failed"

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        user_data = db_client.verify_token(auth_token)
        if await db_client.mark_today(user_data["username"]):
            return "marked today"
    return "failed"


@app.route("/today", methods=['GET'])
async def get_today_status():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    streak = await db_client.get_today(username)
    return str(streak)


@app.route("/today/verbose", methods=['GET'])
async def get_today_status_verbose():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    streak = await db_client.get_today(username)
    if streak == 0: 
        return {
            "today": False,
            "streak": streak
        } 
    else:
        return {
            "today": True,
            "streak": streak
        }

@app.route("/leaderboard", methods=['GET'])
async def get_leaderboard():
    limit_req = request.args.get('limit')
    limit = 5
    if limit_req != None and limit_req.isnumeric():
        limit = int(limit_req)

    toplist = await db_client.leaderboard(limit)
    return {
        "leaderboard": toplist
    }


@app.route("/history", methods=['GET'])
async def get_history():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    streak = await db_client.userhistory(username)
    return str(streak)

@app.route("/register", methods=['POST'])
async def register():
    username = request.json['user']
    password = request.json['pass']

    return await db_client.register(username, password)

@app.route("/login", methods=['GET', 'POST'])
async def login():
    username = request.json['user']
    password = request.json['pass']

    token = await db_client.verify_login(username, password)
    if token:
        return token
    else:
        return

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)