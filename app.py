import os

from flask import Flask
from flask import request
from flask import render_template
from flask import redirect

from flask import url_for

from flask_cors import CORS
from flask import Response
from flask import send_from_directory

from flask_login import LoginManager
from flask_login import login_user, logout_user
from flask_login import current_user
from flask_login import login_required

import json

import db_client


API_URL = os.environ['API_URL']
BASE_URL = os.environ['BASE_URL']

login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

CORS(app)
login_manager.init_app(app)

app.config['CORS_HEADERS'] = 'Content-Type'



@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

### API ROUTES ###

import api_controller
import api_service
import user_service
from user_service import User

from utils import *

@login_manager.user_loader
def load_user(user_id):
    return user_service.get_user_by_id(user_id)

@app.route("/api/mark", methods=['GET', 'POST'])
def mark_today_read_login_route():
    return api_controller.mark_today_read_login_controller(request)

@app.route("/api/mark-with-token", methods=['GET', 'POST'])
def mark_today_read_token_route():
    return api_controller.mark_today_read_token_controller(request)

@app.route("/api/today", methods=['GET'])
def get_today_status_route(): 
    return api_controller.get_today_status_controller(request)

@app.route("/api/today/verbose", methods=['GET'])
def get_today_status_verbose_route():
    return api_controller.get_today_status_verbose_controller(request)

@app.route("/api/leaderboard", methods=['GET'])
def get_leaderboard():
    return api_controller.get_leaderboard_controller(request)

@app.route("/api/history", methods=['GET'])
def get_history():
    return api_controller.get_history_controller(request)

@app.route("/api/register", methods=['POST'])
def register():
    return api_controller.register_controller(request)

@app.route("/api/login", methods=['GET', 'POST'])
def login():
    return api_controller.login_controller(request)

@app.route("/api/logout", methods=['GET', 'POST'])
def logout_api():
    return api_controller.logout_controller(request)


### TEMPLATE ROUTES ###

@app.route("/logout")
@login_required
def logout():
    api_service.logout_service(current_user.username, current_user.api_token)
    logout_user()
    return redirect(url_for("landing_page"))

@app.route("/", methods=['GET', 'POST'])
def landing_page():

    if not current_user or not current_user.is_authenticated:
        return login_page()

    if current_user.username:
        return redirect(url_for("home_page_route"))   # home_page(current_user.username)
    else: 
        return login_page()

@app.route("/register", methods=['GET', 'POST'])
def register_page():

    username, password = None, None

    if request.form:
        username = request.form['username']
        password = request.form['password']

    if username and password:
        data = api_service.register_service(username, password)
        
        return redirect(url_for("landing_page"), code=302)

    return render_template("register.html")

@app.route("/home",methods=['GET', 'POST'])
@login_required
def home_page_route():
    streak = api_service.get_today_status_verbose_service(current_user.username)
    history = api_service.get_history_service(current_user.username)
    return render_template("home.html", 
        api_url=API_URL,
        api_token=current_user.api_token,
        username=current_user.username,
        streak=streak["streak"],
        today=streak["today"],
        history=json.dumps(history),
        note=streak["note"],
        )

def home_page():
    # streak=api_service.get_today_status_verbose_service(username)
    return render_template("home.html", api_url=API_URL, streak=1, eee=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login_page():

    username, password, remember = None, None, False

    if request.method == 'POST':
        if request.form:
            username = request.form['username']
            password = request.form['password']
            remember = request.form['remember'] == 'on'

        string_valid = login_valid(username, password)

        if string_valid:
            data = api_service.login_with_data_service(username, password)

            if data != None:
                login_user(User(data["username"], data["passwordhash"], data["id"], data["token"]), remember=remember)

                return redirect(url_for("home_page_route"), code=302)
            else:
                return redirect(url_for("login_page", status="failed"))

    error_msg = None
    if request.args and request.args.get("status") == "failed":
        error_msg = "incorrect credentials"

    return render_template("login.html", error=error_msg)
