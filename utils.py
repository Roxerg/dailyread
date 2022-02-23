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

    

# book info validation

def partial_word_capitalization(name):
    name = name.replace('`', '\'')

    for sep in ['\'', '`', '-']:
        split_word = name.split(sep)
        if len(split_word) != 1:
            name = sep.join(list(map(lambda x: x.capitalize(), split_word)))
    
    name = re.sub('^([mM][aA]?[Cc])([A-Za-z]+)', lambda x: x.group(1).capitalize() + x.group(2).capitalize(), name)

    return name

def process_author(name):
    name = ' '.join(list(map(lambda x: partial_word_capitalization(x.capitalize()), name.split(' '))))
    name = ' '.join(list(map(lambda x: x+"." if len(x) == 1 else x, name.split(' '))))

    return name

def capitalize_with_exceptions(word):
    exceptions = ['a', 'an', 'the', 'of', 'over', 'by', 'as', 'over']
    if not word in exceptions:
        return word.capitalize()
    else:
        return word

def process_title(title):
    title = ' '.join(list(map(lambda x: capitalize_with_exceptions(x), title.split(' '))))
    
    # capitalize the first word either way
    title_split = title.split(' ')
    title_split[0] = title_split[0].capitalize()
    title = ' '.join(title_split)
    
    return title
