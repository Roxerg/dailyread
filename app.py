from flask import Flask
from flask import request
from flask import render_template


from flask_cors import CORS

import db_client

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


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
        user_data = await db_client.verify_token(auth_token)
        if await db_client.mark_today(user_data["username"]):
            return "marked today"
    return "failed"


@app.route("/today", methods=['GET'])
async def get_today_status():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    res = await db_client.get_today(username)
    return str(res["streak"])


@app.route("/today/verbose", methods=['GET'])
async def get_today_status_verbose():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    res = await db_client.get_today(username)
    if res == None: 
        return {
            "today": False,
            "streak": 0,
        } 
    else:
        return {
            "today": res['today'],
            "streak": res['streak'],
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

@app.route("/api/register", methods=['POST'])
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


@app.route("/", methods=['GET'])
async def login_page():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return render_template("login.html")

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        user_data = await db_client.verify_token(auth_token)
        if user_data["username"]:
            return render_template("home.html")
        else: 
            return render_template("login.html")

@app.route("/register", methods=['GET'])
async def register_page():
    return render_template("register.html")
        

@app.route("/home", methods=['GET'])
async def home_page():
    return render_template("home.html")


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)

