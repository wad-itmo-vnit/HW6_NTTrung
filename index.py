from flask import Flask, request, render_template, make_response, redirect, flash, send_from_directory
import app_config
from model.user import User                                                             # chi can moi class User nen dung from thay vi import
from functools import wraps
import os
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SECRET_KEY'] = app_config.SECRET_KEY                                        # Can dung den cookie nen phai co SECRET_KEY
app.config["MONGO_URI"] = "mongodb://localhost:27017/hoche"
mongo = PyMongo(app)
db = mongo.db

def check_cookie(request):
    return User.get_user(db, request.cookies.get('username')).authorize(request.cookies.get('token'))       # luu 2 thong tin la username va token, vi trong backend xu li nhieu thong tin, vi du nhu hash token truoc khi gui den cho nguoi dung, thi viec dung token do de tim lai trong CSDL rat kho, con username la cai k the giau vi tren ung dung nao cung xuat hien cai do, nen dung username cho nhanh

# DECORATOR:
def login_required(func):
    @wraps(func)
    def login_func(*arg, **kwargs):
        # phai dung try, catch vi chua xu li truong hop chua co cookie
        try:
            if check_cookie(request):
                return func(*arg, **kwargs)
        except:
            pass
        flash("Login required!!!")
        return redirect('/login')
    return login_func

def no_login(func):
    @wraps(func)
    def no_login_func(*arg, **kwargs):
        try:
            if check_cookie(request):                    # dang nhap roi thi redirect ve home
                flash("You're already in!")
                return redirect('/')
        except:
            pass
        return func(*arg, **kwargs)
    return no_login_func

@app.route('/')
def home():
    return redirect('/index')

@app.route('/index')
@login_required                                                                     # can login_required
def index():
    return render_template('index.html', text="Welcome!!!")

@app.route('/login', methods=['POST', 'GET'])
@no_login
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # Post request se gui den 2 thong tin la username va password, dau tien phai lay thong tin ra
    # O day chi xu li de thuc hien chuc nang, chu k bao dam an toan cho ung dung
    # Thuc te thi phai kiem tra nhung du lieu do co dung k.
    username, password = request.form.get('username'), request.form.get('password')

    # truoc tien nguoi dung can dang nhap, roi moi xu li den phan authorize, nen co phan o duoi day
    if User.find_user(db, username):                                                    # kiem tra user co hay k
        current_user = User.get_user(db, username)
        if current_user.authenticate(password):                                  # neu dung nua thi tien hanh set cookie, bao nguoi dung da dang nhap
            token = current_user.init_session()                                  # co the su dung current_user thay vi su dung truc tiep tu trong mang nhu o day, init_session(): tao token, luu token vao trong object user do, va tra ve token cho chung ta
            resp = make_response(redirect('/index'))
            resp.set_cookie('username', username)
            resp.set_cookie('token', token)
            return resp
        else:
            flash("Username or password is not correct!!!")
    else:
        flash("User does not exist")
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required                                                                     # Chi gui yeu cau thoat dang nhap khi da dang nhap
def logout():
    username = request.cookies.get('username')                                      # da co token, username o trong cookie
    current_user = User.get_user(db, username)
    current_user.terminate_session()
    resp = make_response(redirect('/login'))
    resp.delete_cookie('username')
    resp.delete_cookie('token')
    flash("You've logged out!!!")
    return resp

@app.route('/register', methods=['POST', 'GET'])
@no_login
def register():
    if request.method == "GET":
        return render_template('register.html')
    
    # POST
    username, password, password_confirm = request.form.get('username'), request.form.get('password'), request.form.get('password_confirm')
    if not User.find_user(db, username):
        if password == password_confirm:
            new_user = User.new(db, username,password)
            token = new_user.init_session()                                  # dang ki
            resp = make_response(redirect('/index'))                                # xong
            resp.set_cookie('username', username)                                   # thi
            resp.set_cookie('token', token)                                         # dang nhap
            return resp                                                             # luon
        else:
            flash("Passwords don't match!!!")
    else:
        flash("User already exists!!!")  
    return render_template('register.html')                                         # GET request

# UPDATE password:
@app.route('/changepwd', methods=["POST", "GET"])
@login_required
def changepwd():
    if request.method =="GET":
        return render_template("changepwd.html")
    username = request.cookies.get("username")
    old_pwd = request.form.get("old_pwd")
    new_pwd = request.form.get("new_pwd")
    new_pwd_confirm = request.form.get("new_pwd_confirm")

    current_user = User.get_user(db, username)
    if current_user.authenticate(old_pwd):
        if new_pwd == new_pwd_confirm:
            if new_pwd == old_pwd:
                flash("Still old password!!!")
                return redirect("/")
            else:
                current_user.update_password(new_pwd)
                flash("Password updated successfully!!!")
                return redirect("/")
        else:
            flash("New password not match!!!")
    else:
        flash("Old password is not correct!!!")
    return render_template("changepwd.html")

def allowed_extension(file_name):
    EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    extension = file_name.split('.')[-1].lower()
    return extension in EXTENSIONS

@app.route('/uploadAvatar', methods=['GET', 'POST'])
@login_required
def handle_upload_avatar():
    username = request.cookies.get("username")
    current_user = User.get_user(db,username)
    if request.method == 'GET':
        user_avatar = current_user.get_avatar()
        return render_template("avatar.html", user_avatar = user_avatar)

    if 'avatar-image' not in request.files:
        flash("File not found!!!")
        return redirect('/uploadAvatar')

    file = request.files['avatar-image']
    # dam bao cho ng dung chi duoc up anh len
    # neu k chon file
    if file.filename == '':
        flash("No file selected!!!")
        return redirect('/uploadAvatar')
    # neu file k duoc chap nhan
    if not allowed_extension(file.filename):
        flash("Invalid file extension!!!")
        return redirect('/uploadAvatar')
    
    # secure_filename: dam bao filename luu trong he thong thi se k gap truc trac
    file_name = current_user.username + "_" + secure_filename(file.filename)
    
    # De phong CSDL bi loi, hoac lag --> dung try
    try:
        user_avatar = current_user.get_avatar()
        # Delete old avatar
        try:
            if user_avatar != 'default.png':
                id = mongo.db.fs.files.find_one({"filename": user_avatar}).get('_id')
                mongo.db.fs.chunks.remove({'files_id': id})
                mongo.db.fs.files.remove({'_id': id})
        except:
            flash("Avatar is not in database!!!")
        
        mongo.save_file(file_name, file)
        current_user.set_avatar(file_name)
    except:
        flash("Avatar upload success!!!")
        return redirect('/uploadAvatar')

    flash("Avatar upload success!!!")
    return redirect('/uploadAvatar')

@app.route('/uploads/<filename>')
@login_required
def serve_uploaded(filename):
    if filename == 'default.png':
        return app.send_static_file(filename)
    return mongo.send_file(filename)

@app.route('/Sheva', methods=["GET"])
def sheva():
    if request.method =="GET":
        return render_template("Sheva.html")
    return render_template("Sheva.html")

if __name__ == '__main__':
    app.run(host='localhost', port=80, debug=True)
    # Thuc te thi co the doi localhost -> mang LAN, port co the = 5000
    # debug = True , tuc la khi sua lai code va luu thi trang web tu sua lai roi, k can phai chay lai "py index.py" nua