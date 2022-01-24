from flask import Flask
from flask import request
import db_client

app = Flask(__name__)

@app.route("/mark")
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

@app.route("/today")
async def get_today_status():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    streak = await db_client.get_today(username)
    return str(streak)

@app.route("/today/verbose")
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

@app.route("/leaderboard")
async def get_leaderboard():
    limit_req = request.args.get('limit')
    limit = 5
    if limit_req != None and limit_req.isnumeric():
        limit = int(limit_req)

    toplist = await db_client.leaderboard(limit)
    return {
        "leaderboard": toplist
    }

@app.route("/register")
async def register():
    username = request.json['user']
    password = request.json['pass']

    return await db_client.register(username, password)

@app.route("/history")
async def get_history():
    username = request.args.get('user')
    if username == None:
        return "need to specify user"

    streak = await db_client.userhistory(username)
    return str(streak)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)