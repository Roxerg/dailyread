import os

from flask import Flask
from flask import request
from flask import render_template

from flask_cors import CORS
from flask import Response

import db_client

API_URL = os.environ['API_URL']

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# API ROUTES


@app.route("/api/mark", methods=['GET', 'POST'])
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
    return error_response("unauthorized")

@app.route("/api/mark-with-token", methods=['GET', 'POST'])
async def mark_today_read_token():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return error_response("unauthorized")

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        user_data = await db_client.verify_token(auth_token)
        if await db_client.mark_today(user_data["username"]):
            return "marked today"
    return error_response("unauthorized")


@app.route("/api/today", methods=['GET'])
async def get_today_status():
    username = request.args.get('user')
    if username == None:
        return error_response("user not specified", status=400)

    res = await db_client.get_today(username)
    return str(res["streak"])


@app.route("/api/today/verbose", methods=['GET'])
async def get_today_status_verbose():
    username = request.args.get('user')
    if username == None:
        return error_response("user not specified", status=400)

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

@app.route("/api/leaderboard", methods=['GET'])
async def get_leaderboard():
    limit_req = request.args.get('limit')
    limit = 5
    if limit_req != None and limit_req.isnumeric():
        limit = int(limit_req)

    toplist = await db_client.leaderboard(limit)
    return {
        "leaderboard": toplist
    }


@app.route("/api/history", methods=['GET'])
async def get_history():
    username = request.args.get('user')
    if username == None:
        return error_response("user not specified", status=400)

    streak = await db_client.userhistory(username)
    return str(streak)

@app.route("/api/register", methods=['POST'])
async def register():
    username = request.json['user']
    password = request.json['pass']

    return await db_client.register(username, password)

@app.route("/api/login", methods=['GET', 'POST'])
async def login():
    username = request.json['user']
    password = request.json['pass']

    token = await db_client.verify_login(username, password)
    if token:
        return token
    else:
        return error_response("login failed, credentials not found")

@app.route("/api/logout", methods=['GET', 'POST'])
async def logout():
    auth_header = request.headers.get('Authorization')
    username = request.args.get('user')

    if not auth_header:
        return "failed"

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        await db_client.logout(username, auth_token)
        return no_content_response()
    return error_response("logout failed, token not deleted")


# TEMPLATE ROUTES

@app.route("/", methods=['GET'])
async def landing_page():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return await login_page()

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        user_data = await db_client.verify_token(auth_token)
        if user_data["username"]:
            return await home_page()
        else: 
            return await login_page()

@app.route("/register", methods=['GET'])
async def register_page():
    return render_template("register.html", api_url=API_URL)
        

@app.route("/home", methods=['GET'])
async def home_page():
    return render_template("home.html", api_url=API_URL)

@app.route("/login", methods=['GET'])
async def login_page():
    return render_template("login.html", api_url=API_URL)


def no_content_response():
    return Response(status=204)

def error_response(content=None, status=401, mimetype="application/json"):
    if content != None:
        return Response(content, status=status, mimetype=mimetype)
    else:
        return Response(status=status, mimetype=mimetype)