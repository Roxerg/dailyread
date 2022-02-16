
import db_client
from utils import *

from flask_login import login_user
from user_service import User

def mark_today_read_login_service(username, password):
    valid = db_client.verify_login(username, password)
    if valid:
        return db_client.mark_today(username)
    return error_response("unauthorized")

def mark_today_read_token_service(auth_token, advanced_data=None):
    if auth_token:
        user_data = db_client.verify_token(auth_token)
        return db_client.mark_today(user_data["username"], advanced_data)
    return error_response("unauthorized")

def get_today_status_service(username):
    res = db_client.get_today(username)
    return str(res["streak"])

def get_today_status_verbose_service(username):
    res = db_client.get_today(username)
    if res == None: 
        return {
            "today": False,
            "streak": 0,
            "note": None,
        } 
    else:
        return {
            "today": res['today'],
            "streak": res['streak'],
            "note": res['note'],
        }


def get_leaderboard_service(leaderboard_type, limit):
    if leaderboard_type in ["overall", "alltime"]:
        return {
            "leaderboard_overall": db_client.leaderboard_overall(limit)
        }
    elif leaderboard_type in ["ongoing", "current"]:
        return {
            "leaderboard_ongoing": db_client.leaderboard_ongoing(limit)
        }
    else:
        return {
            "leaderboard_ongoing" : db_client.leaderboard_ongoing(limit),
            "leaderboard_overall" : db_client.leaderboard_overall(limit)
        }

def get_history_service(username):
    streak = db_client.userhistory(username)
    
    response = list(map(lambda x : {
        "day": x[1].strftime('%d-%m-%Y'),
        "streak" : x[0],
    }, streak))
    return { "history": response }


def register_service(username, password):
    if db_client.register(username, password):
        return "registration successful"
    else:
        return error_response("username taken", status=409)

def login_service(username, password):
    token = db_client.verify_login(username, password)
    if token:
        return token
    else:
        return error_response("login failed, credentials not found")

def login_with_data_service(username, password):
    data = db_client.verify_login_returning_data(username, password)
    if data:
        return data
    else:
        return None
    
    

def logout_service(username, auth_token):
    if auth_token:
        db_client.logout(username, auth_token)
        return no_content_response()
    return error_response("logout failed, token not deleted")