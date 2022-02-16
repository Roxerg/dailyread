
import api_service
from utils import *
from flask_login import login_user

def mark_today_read_login_controller(request):
    if request.json == None:
        return "body must contain login (user, pass)"

    if not 'user' in request.json or not 'pass' in request.json:
        return "body must contain login (user, pass)"

    username, password = get_credentials(request)

    return api_service.mark_today_read_login_service(username, password)


def mark_today_read_token_controller(request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return error_response("no auth")

    advanced_data = None
    if request.json:
        advanced_data = request.json

    auth_token = auth_header.split(" ")[1]

    res = api_service.mark_today_read_token_service(auth_token, advanced_data)
    return { "marked" : res }

def get_today_status_controller(request):
    username = request.args.get('user')
    if username == None:
        return error_response("user not specified", status=400)

    return api_service.get_today_status_service(username)

def get_today_status_verbose_controller(request):
    username = request.args.get('user')
    if username == None:
        return error_response("user not specified", status=400)

    return api_service.get_today_status_verbose_service(username)

def get_leaderboard_controller(request):
    leaderboard_type = request.args.get('type')
    limit_req = request.args.get('limit')
    limit = 5
    if limit_req != None and limit_req.isnumeric():
        limit = int(limit_req)

    return api_service.get_leaderboard_service(leaderboard_type, limit)

def get_history_controller(request):
    username = request.args.get('user')

    if not input_check(username):
        return error_response(status=400)

    if username == None:
        return error_response("user not specified", status=400)

    return api_service.get_history_service(username)


def register_controller(request):
    username, password = get_credentials(request)

    if not login_valid(username, password):
        return error_response("credentials not valid", status=400)


def login_controller(request):
    username, password = get_credentials(request)

    if not login_valid(username, password):
        return error_response(status=400)

    return api_service.login_service(username, password)


def logout_controller(request):
    auth_header = request.headers.get('Authorization')
    username = request.args.get('user')

    if not input_check(username):
        return error_response(status=400)

    if not auth_header:
        return "failed"

    auth_token = auth_header.split(" ")[1]

    return api_service.logout_service(username, auth_token)