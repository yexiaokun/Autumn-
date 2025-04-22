import os
from flask import Blueprint,render_template, jsonify,redirect,url_for,session,g,request
from exts import mail,db
from flask_mail import Message
import string
import random
from models import EmailCaptchaModel,UserModel,QuestionModel
from .forms import RegisterForm,LoginForm,UpdateAvatarForm,UpdatePasswordForm,UpdateUsernameForm
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from decorators import login_required
from sqlalchemy import desc
from flask_sqlalchemy import pagination

bp = Blueprint("auth",__name__,url_prefix="/auth")

@bp.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
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
                return render_template("login.html",error = error_message)
            if check_password_hash(user.password,password):
                #cookie:
                #cookie中不适合存储太多数据，只适合存储少量数据
                #cookie一般用来存放登录授权的东西
                #flask中的session,是经过加密存储在cookie中的
                session['user_id'] = user.id
                return redirect("/")
            else:
                print("密码错误!")
                return render_template("login.html",error="密码有误,请重试!",email=email)
        else:
            # print(form.errors)
            # return render_template("login.html",error="输入信息有误,请检查后再试!")
            error_message=[]
            for field,errors in form.errors.items():
                for error in errors:
                    error_message.append(f"{error}")
            error = "<br>".join(error_message)
            email = request.form.get('email')
            return render_template("login.html",error=error,email=email)



@bp.route("/register",methods=['GET','POST'])
def register():
    #验证用户提交的邮箱和验证码是否对应且正确
    #表单验证:flask-wtf:wtforms
    if request.method == 'GET':
        return render_template("register.html")
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
                return render_template("register.html", error="该邮箱已被注册，请使用其他邮箱。",email=email,username=username)
            # 检查用户名是否已存在
            username_exists = UserModel.query.filter_by(username=username).first()
            if username_exists:
                return render_template("register.html", error="该用户名已被使用，请选择其他用户名。",email=email,username=username)
            user = UserModel(email=email,username=username,password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            
            login_url = url_for('auth.login')
            error_message = f"注册成功,是否要去<a href='{login_url}'>登录</a>?"
            return render_template("login.html",error = error_message)
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
            return render_template("register.html",error=error,email=email,username=username,password=password,password_confirm=password_confirm)


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
    #memcached/redis
    #用数据库表的方式存储
    email_captcha = EmailCaptchaModel(email=email,captcha=captcha)
    db.session.add(email_captcha)
    db.session.commit()
    #RESTful API
    #{code:200/400/500,message:"",data:{}}
    return jsonify({"code":200,"message":"","data":None})

@bp.route("/mail/test")
def mail_test():
    message = Message(subject="邮箱测试",recipients=["1667877328@qq.com"],body="这是一条测试邮件")
    mail.send(message)
    return "邮件发送成功!"


        
        
@bp.route("/user_info", methods=['GET', 'POST'])
@login_required
def user_info():
    user = g.user
    
    user_ip = request.remote_addr
    #获取当前页码，默认为1
    page = request.args.get('page',1,type=int)
    per_page = 5
    questions_pagination = QuestionModel.query.filter_by(author=user).order_by(desc(QuestionModel.create_time)).paginate(page=page,per_page=per_page,error_out=False) # 直接使用 user.questions
    questions = questions_pagination.items
    if request.method == 'GET':
        return render_template("user_info.html", user=user, questions=questions,user_ip=user_ip,pagination = questions_pagination)
    else:
        # 处理修改用户名
        username_form = UpdateUsernameForm(request.form)
        if username_form.validate():
            new_username = username_form.username.data
            user.username = new_username
            db.session.commit()
            return redirect(url_for('auth.user_info'))

        # 处理修改密码
        password_form = UpdatePasswordForm(request.form)
        if password_form.validate():
            old_password = password_form.old_password.data
            new_password = password_form.new_password.data
            if check_password_hash(user.password, old_password):
                user.password = generate_password_hash(new_password)
                db.session.commit()
                return redirect(url_for('auth.user_info'))
            else:
                return render_template("user_info.html", user=user, questions=questions, password_error="旧密码输入错误")

        # 处理修改头像
        avatar_form = UpdateAvatarForm(request.files)
        if avatar_form.validate():
            avatar = avatar_form.avatar.data
            if avatar:
                #获取当前文件所在的目录
                base_dir = os.path.dirname(os.path.abspath(__file__))
                # 拼接 uploads 文件夹的绝对路径
                upload_dir = os.path.join(base_dir, '../uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(upload_dir, filename))
                user.avatar = filename
                db.session.commit()
                return redirect(url_for('auth.user_info'))

        return render_template("user_info.html", user=user, questions=questions,user_ip=user_ip)
    

@bp.route("/delete_question/<int:question_id>",methods=['POST'])
@login_required
def delete_question(question_id):
    question = db.session.get(QuestionModel,question_id)
    if question and question.author == g.user:
        db.session.delete(question)
        db.session.commit()
    return redirect(url_for('auth.user_info'))