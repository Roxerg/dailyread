
import db_client

class User:

    def __init__(self, username, password_hash, id, api_token):
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

        self.username = username
        self.id = id
        self.password_hash = password_hash
        self.api_token = api_token


    def get_id(self):
        return self.id
        


def get_user_by_id(user_id):
    user = db_client.get_user_by_id(user_id)
    token = db_client.get_token_by_id(user_id)
    
    if user == None:
        return None
    
    return User(user[1], user[2], user[0], token)
