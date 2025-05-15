import os,requests
from flask import Blueprint,render_template, jsonify,redirect,url_for,session,g,request,abort
from exts import mail,db
from flask_mail import Message
import string,random,threading,time
from models import EmailCaptchaModel,UserModel,QuestionModel,FollowModel,LikeModel
from .forms import RegisterForm,LoginForm,UserInfoForm,ForgotPasswordForm,ResetPasswordForm
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from decorators import login_required
from sqlalchemy import desc
from flask_sqlalchemy import pagination
from datetime import datetime,timedelta

bp = Blueprint("auth",__name__,url_prefix="/auth")

@bp.route("/login",methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template("login.html",form=form)
    else:
        form = LoginForm(request.form)
        if form.validate():
            email = form.email.data
            password = form.password.data
            user = UserModel.query.filter_by(email=email).first()
            if not user:
                print("邮箱在数据库中不存在!")
                register_url = url_for('auth.register')
                error_message = f"邮箱不存在，是否要去<a href='{register_url}'>注册</a>?"
                return render_template("login.html",error = error_message,form=form)
            if check_password_hash(user.password,password):
                #cookie:
                #cookie中不适合存储太多数据，只适合存储少量数据
                #cookie一般用来存放登录授权的东西
                #flask中的session,是经过加密存储在cookie中的
                session['user_id'] = user.id
                return redirect("/")
            else:
                print(form.errors)
                print("密码错误!")
                return render_template("login.html",error="密码有误,请重试!",email=email,form=form)
        else:
            print(form.errors)
            # return render_template("login.html",error="输入信息有误,请检查后再试!")
            error_message=[]
            for field,errors in form.errors.items():
                for error in errors:
                    error_message.append(f"{error}")
            error = "<br>".join(error_message)
            email = request.form.get('email')
            return render_template("login.html",error=error,email=email,form=form)



location = "未知城市"
def get_location():
    #声明location为全局变量
    global location
    #获取用户IP地址
    user_ips = ["123.160.172.12","123.112.0.16","124.207.0.0"]
    user_ip = random.choice(user_ips)
    #user_ip = request.remote_addr
    print(f"用户IP地址: {user_ip}") #打印用户IP地址
    #调用高德IP定位API
    amap_key = os.getenv('AMAP_KEY')
    print("高德API密钥:", amap_key) #打印高德API密钥
    IP_url = f"https://restapi.amap.com/v3/ip?ip={user_ip}&key={amap_key}"
    try:
        response = requests.get(IP_url)
        print(f"请求状态码: {response.status_code}") #打印请求状态码
        print(f"响应数据: {response.text}") #打印响应数据
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                city = data.get('city')
                if city:
                    location = city
                else:
                    location = "未知城市"
            else:
                location = "未知城市"
        else:
            location = "未知城市"
    except Exception as e:
        print(f"获取地理位置信息时出错：{e}")
        location = "未知城市"
    return location
def update_location():
    # 定时更新用户地理位置
    while True:
        get_location()
        time.sleep(6000)  # 每60秒更新一次
update_thread = threading.Thread(target=update_location)
update_thread.daemon = True
update_thread.start()
# 定义一个路由，返回用户的地理位置信息
@bp.route("/api/get_location",methods=['GET'])
def api_get_location():
    return jsonify({"location": location})




@bp.route("/register",methods=['GET','POST'])
def register():
    #验证用户提交的邮箱和验证码是否对应且正确
    #表单验证:flask-wtf:wtforms
    form = RegisterForm()
    if request.method == 'GET':
        return render_template("register.html",form=form)
    else:
        form = RegisterForm(request.form)
        if form.validate():
            email = form.email.data
            username = form.username.data
            password = form.password.data
            password_confirm = form.password_confirm.data
            # 检查邮箱是否已存在
            email_exists = UserModel.query.filter_by(email=email).first()
            if email_exists:
                return render_template("register.html", error="该邮箱已被注册，请使用其他邮箱。",email=email,username=username,form=form)
            # 检查用户名是否已存在
            username_exists = UserModel.query.filter_by(username=username).first()
            if username_exists:
                return render_template("register.html", error="该用户名已被使用，请选择其他用户名。",email=email,username=username,form=form)
            user = UserModel(email=email,username=username,password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            
            login_url = url_for('auth.login')
            error_message = f"注册成功,是否要去<a href='{login_url}'>登录</a>?"
            return render_template("login.html",error = error_message,form=form)
        else:
            error_message = []
            for field,errors in form.errors.items():
                for error in errors:
                    error_message.append(f"{error}")
            error = "<br>".join(error_message)
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            return render_template("register.html",error=error,email=email,username=username,password=password,password_confirm=password_confirm,form=form)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")



#如果没有指定methods参数，默认就是GET请求
@bp.route("/captcha/email")
def get_email_captcha():
    # /captcha/email/<email>
    # /captcha/email?email=xxx@qq.com
    email = request.args.get("email")
    #4/6:随机数字，字母，数字和字母的组合
    source = string.digits*4
    captcha = random.sample(source,4)
    captcha = "".join(captcha) 
    message = Message(subject="知了传课注册验证码",recipients=[email],body=f"您的验证码是:{captcha}")
    mail.send(message)
    
    #删除旧的验证码记录
    old_captchas = EmailCaptchaModel.query.filter_by(email=email).all()
    for old_captcha in old_captchas:
        db.session.delete(old_captcha)
    
    #memcached/redis
    #用数据库表的方式存储
    email_captcha = EmailCaptchaModel(email=email,captcha=captcha)
    db.session.add(email_captcha)
    db.session.commit()
    #RESTful API
    #{code:200/400/500,message:"",data:{}}
    return jsonify({"code":200,"message":"","data":None})


        
        
@bp.route("/user_info/<int:user_id>", methods=['GET', 'POST'])
@login_required
def user_info(user_id):
    user = UserModel.query.get(user_id)
    #处理用户不存在的情况
    if not user:
        abort(404)
    user_ip = request.remote_addr
    #获取当前页码，默认为1
    page = request.args.get('page',1,type=int)
    per_page = 5
    questions_pagination = QuestionModel.query.filter_by(author=user).order_by(desc(QuestionModel.create_time)).paginate(page=page,per_page=per_page,error_out=False) # 直接使用 user.questions
    questions = questions_pagination.items
    
    #查询该用户收到的所有点赞信息
    likes = LikeModel.query.filter((LikeModel.question.has(author=user)) | 
                                    (LikeModel.comment.has(author=user))
                                    ).all()
    liker_usernames = [like.user.username for like in likes]
    #初始化表单
    form = UserInfoForm(request.form,obj=user,**request.files.to_dict())
    if request.method == 'GET':
        return render_template("user_info.html", user=user, questions=questions,user_ip=user_ip,pagination = questions_pagination,
                                liker_usernames=liker_usernames,
                                form=form)
    else:
        if form.validate():
            # 处理修改用户名
            if form.username.data:
                user.username = form.username.data

            # 处理修改性别
            if form.gender.data:
                user.gender = form.gender.data

            # 处理修改年龄
            if form.age.data:
                user.age = form.age.data

            # 处理修改出生日期
            if form.birth_date.data:
                user.birth_date = form.birth_date.data
                
            # 处理修改密码
            old_password = form.old_password.data
            new_password = form.new_password.data
            confirm_new_password = form.confirm_new_password.data
            if old_password and new_password and confirm_new_password:
                if check_password_hash(user.password, old_password):
                    user.password = generate_password_hash(new_password)
                else:
                    return render_template("user_info.html", user=user, user_ip=user_ip, questions=questions,
                                            pagination=questions_pagination, password_error="旧密码输入错误", form=form)

            # 处理修改头像
            avatar = form.avatar.data
            if avatar:
                # 获取当前文件所在的目录
                base_dir = os.path.dirname(os.path.abspath(__file__))
                # 拼接 uploads 文件夹的绝对路径
                upload_dir = os.path.join(base_dir, '../uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(upload_dir, filename))
                user.avatar = filename

            try:
                db.session.commit()
                print("数据更新成功")
                return redirect(url_for('auth.user_info', user_id=user_id))
            except Exception as e:
                print(f'数据更新失败:{e}')
                db.session.rollback()
                return redirect(url_for('auth.user_info', user_id=user_id))

        return render_template("user_info.html", user=user, questions=questions, user_ip=user_ip, pagination=questions_pagination,
                                liker_usernames=liker_usernames, form=form)
    

@bp.route("/delete_question/<int:question_id>",methods=['POST'])
@login_required
def delete_question(question_id):
    question = db.session.get(QuestionModel,question_id)
    if question and question.author == g.user:
        db.session.delete(question)
        db.session.commit()
    return redirect(url_for('auth.user_info'),user_id=g.user.id)

@bp.route("/follow",methods=['PUT'])
@login_required
def follow():
    user_id = request.json.get('user_id')
    followed = UserModel.query.get(user_id)
    if followed:
        follow = FollowModel.query.filter_by(follower_id=g.user.id,followed_id=user_id).first()
        if not follow:
            new_follow = FollowModel(follower_id=g.user.id,followed_id=user_id)
            db.session.add(new_follow)
            db.session.commit()
            return jsonify({'success':True})
    return jsonify({'success':False})

@bp.route("/unfollow",methods=['PUT'])
@login_required
def unfollow():
    user_id = request.json.get('user_id')
    followed = UserModel.query.get(user_id)
    if followed:
        follow = FollowModel.query.filter_by(follower_id=g.user.id,followed_id=user_id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return jsonify({'success':True})
    return jsonify({'success':False})

@bp.route("/forgot_password",methods=['GET','POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if request.method == 'GET':
        return render_template("forgot_password.html",form=form)
    else:
        form = ForgotPasswordForm(request.form)
        if form.validate():
            email = form.email.data
            session['reset_email'] = email  #存储用户邮箱到session中
            #验证通过，跳转到修改密码页面
            return redirect(url_for('auth.reset_password',email=email,form=form))
        else:
            error_message = []
            for field,errors in form.errors.items():
                for error in errors:
                    error_message.append(f"{error}")
            error = "<br>".join(error_message)
            email = request.form.get('email')
            return render_template("forgot_password.html",error=error,email=email,form=form)

@bp.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.login'))  # 如果 session 中没有邮箱信息，跳转到登录页面

    user = UserModel.query.filter_by(email=email).first()
    if not user:
        return render_template("reset_password.html", error="无效的重置密码请求")
    form = ResetPasswordForm()
    if request.method == 'GET':
        return render_template("reset_password.html",form=form)
    else:
        form = ResetPasswordForm(request.form)
        if form.validate():
            new_password = form.new_password.data
            user.password = generate_password_hash(new_password)
            db.session.commit()
            session.pop('reset_email', None)  # 重置密码成功后，从 session 中移除邮箱信息
            return render_template("reset_password.html", success="密码重置成功，请使用新密码登录",form=form)
        else:
            error_message = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_message.append(f"{error}")
            error = "<br>".join(error_message)
            return render_template("reset_password.html", error=error,form=form)