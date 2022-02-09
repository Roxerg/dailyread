import os

from flask import Flask
from flask import request
from flask import render_template

from flask_cors import CORS
from flask import Response
from flask import send_from_directory

import db_client
import re

API_URL = os.environ['API_URL']

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'



@app.route('/favicon.ico', methods=['GET'])
async def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

### API ROUTES ###


@app.route("/api/mark", methods=['GET', 'POST'])
async def mark_today_read_login():
    if request.json == None:
        return "body must contain login (user, pass)"

    if not 'user' in request.json or not 'pass' in request.json:
        return "body must contain login (user, pass)"

    username, password = get_credentials()

    valid = await db_client.verify_login(username, password)
    if valid:
        return await mark_today_read(user_data["username"])
    return error_response("unauthorized")

@app.route("/api/mark-with-token", methods=['GET', 'POST'])
async def mark_today_read_token():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return error_response("no auth")

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        user_data = await db_client.verify_token(auth_token)
        return await mark_today_read(user_data["username"])
    return error_response("unauthorized")

async def mark_today_read(username):
    if await db_client.mark_today(username):
        return "marked today"
    else:
        return "already marked"

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
    leaderboard_type = request.args.get('type')
    limit_req = request.args.get('limit')
    limit = 5
    if limit_req != None and limit_req.isnumeric():
        limit = int(limit_req)

    if leaderboard_type in ["overall", "alltime"]:
        return {
            "leaderboard_overall": await db_client.leaderboard_overall(limit)
        }
    elif leaderboard_type in ["ongoing", "current"]:
        return {
            "leaderboard_ongoing": await db_client.leaderboard_ongoing(limit)
        }
    else:
        return {
            "leaderboard_ongoing" : await db_client.leaderboard_ongoing(limit),
            "leaderboard_overall" : await db_client.leaderboard_overall(limit)
        }

@app.route("/api/history", methods=['GET'])
async def get_history():
    username = request.args.get('user')

    if not input_check(username):
        return error_response(status=400)

    if username == None:
        return error_response("user not specified", status=400)

    streak = await db_client.userhistory(username)
    
    response = list(map(lambda x : {
        "day": x["day"].strftime('%d-%m-%Y'),
        "streak" : x["streak"],
    }, streak))
    return str(response)

@app.route("/api/register", methods=['POST'])
async def register():
    username, password = get_credentials()

    if not login_valid(username, password):
        return error_response(status=400)


    return await db_client.register(username, password)

@app.route("/api/login", methods=['GET', 'POST'])
async def login():
    username, password = get_credentials()

    if not login_valid(username, password):
        return error_response(status=400)

    token = await db_client.verify_login(username, password)
    if token:
        return token
    else:
        return error_response("login failed, credentials not found")

@app.route("/api/logout", methods=['GET', 'POST'])
async def logout():
    auth_header = request.headers.get('Authorization')
    username = request.args.get('user')

    if not input_check(username):
        return error_response(status=400)

    if not auth_header:
        return "failed"

    auth_token = auth_header.split(" ")[1]

    if auth_token:
        await db_client.logout(username, auth_token)
        return no_content_response()
    return error_response("logout failed, token not deleted")


### TEMPLATE ROUTES ###

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


### UTILS ###

def login_valid(user, pwd):
    return input_check(user) and input_check(pwd)

def input_check(input):
    if len(input) < 3 or len(input) > 32:
        return False
    if re.search(r"[.,;()<>~#\/\\\"\'*$|\[\]\{\} &%]", input) != None:
        return False
    return True

def no_content_response():
    return Response(status=204)

def error_response(content=None, status=401, mimetype="application/json"):
    if content != None:
        return Response(content, status=status, mimetype=mimetype)
    else:
        return Response(status=status, mimetype=mimetype)

def get_credentials():
    username = request.json['user']
    password = request.json['pass']

    return username, password