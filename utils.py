import re
from flask import Response

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

def get_credentials(request):
    username = request.json['user']
    password = request.json['pass']

    return username, password

    
def process_author(name):
    name.split(' ')