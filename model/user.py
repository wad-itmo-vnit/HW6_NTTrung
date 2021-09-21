# MUC DICH: De tao them duoc user, hay luu tru dang nhap voi nhieu user, thi can model user

import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
import app_config
import os

# tao random
def gen_session_token(length = 24):
    token = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(length)])                   # random ra 24 ki tu roi noi chung voi nhau
    return token

class User:                                                     # class User de luu tat ca thong tin ve 1 user
    def __init__(self, db, username, password, token=None, avatar='default.png'):
        self.db = db
        self.username = username
        self.password = password
        self.token = token                                      # de phong truong hop chua tao token ma co yeu cau truy cap den
        self.avatar = avatar

    def get_avatar(self):
        return self.avatar

    def set_avatar(self, file_name):
        self.avatar = file_name
        self.db.users.update_one({"username": self.username}, {
            "$set": {
                "avatar": file_name}
        })
    
    # Truong hop co du lieu moi
    @classmethod
    def new(cls, db, username, password):
        password = generate_password_hash(password)
        # Save to database
        db.users.insert({"username": username, "password": password})
        return cls(db, username, password)
    
    @staticmethod
    def find_user(db, username):
        return len(list(db.users.find({"username": username}))) > 0

    @classmethod
    def get_user(cls, db, username):
        data = db.users.find_one({"username": username})
        return cls(db, data["username"], data["password"], data.get('token', None), data.get('avatar', 'default.png'))

    def authenticate(self, password):
        return check_password_hash(self.password, password)
    
# Dung session_based:
    def init_session(self):
        self.token = gen_session_token()
        
        # update to database
        self.db.users.update_one({"username": self.username}, {"$set": {"token": self.token}})
        return self.token                                               # cai init_session can phai gan gia tri cookie cho client nua
    
    def authorize(self, token):                                         # kiem tra xem chung ta co dung la nguoi dang nhap hay khong, kiem tra trong token gui den cho client, login_required
        return token == self.token
    
    def terminate_session(self):                                        # xoa bo thong tin khi log out
        self.token = None                                               # chi don gian la xoa token di

        # update to database
        self.db.users.update_one({"username": self.username}, {"$set": {"token": None}})
    
    def __str__(self):                                                  # khi ta dung ham str voi doi tuong nay, thi se tra ve cai gi
        return f'{self.username};{self.password};{self.token}'          # ke ca khi reset roi, van co the dang nhap bang cac token duoc cap

#UPDATE password:
    def update_password(self, password):
        self.password = generate_password_hash(password)
        # Update to database
        self.db.users.update_one({"username": self.username}, {"$set": {"password": self.password}})
        