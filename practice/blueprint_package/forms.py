import wtforms
import wtforms.form
from wtforms.validators import Email,Length,EqualTo,InputRequired,Optional
from models import UserModel,EmailCaptchaModel
from exts import db
from wtforms.fields import DateField
from flask_wtf import FlaskForm
from datetime import datetime,timedelta

#Form:主要就是用来验证前端提交的数据是否符合要求
class RegisterForm(FlaskForm):
    email = wtforms.StringField(validators=[Email(message="邮箱格式错误!")])
    captcha = wtforms.StringField(validators=[Length(min = 4,max = 4,message = "验证码格式错误!")])
    username = wtforms.StringField(validators=[Length(min = 3,max = 20,message = "用户名格式错误!")])
    password = wtforms.StringField(validators=[Length(min = 6,max = 20,message = "密码格式错误!")])
    password_confirm = wtforms.StringField(validators=[EqualTo("password",message = "两次密码不一致!")])
    
    #自定义验证:
    #1.邮箱是否已经被注册
    def validate_email(self,field):
        email = field.data 
        user = UserModel.query.filter_by(email=email).first()
        if user:
            raise wtforms.ValidationError(message="该邮箱已被注册!")
    #2.验证码是否正确
    def validate_captcha(self,field):
        captcha = field.data 
        email = self.email.data 
        captcha_model = EmailCaptchaModel.query.filter_by(email=email,captcha=captcha).first()
        if not captcha_model:
            raise wtforms.ValidationError(message="邮箱或验证码错误!")
        
        now = datetime.now()
        if now - captcha_model.create_time > timedelta(minutes=5):
            raise wtforms.ValidationError(message="验证码已过期，请重新获取!")
    
    

class LoginForm(FlaskForm):
    email = wtforms.StringField(validators=[Email(message="邮箱格式错误!")])
    password = wtforms.StringField(validators=[Length(min = 6,max = 20,message = "密码格式错误!")])
    

class QuestionForm(FlaskForm):
    title = wtforms.StringField(validators=[Length(min=1,message="标题格式错误!")])
    content = wtforms.StringField(validators=[Length(min=0,message="内容格式错误!")])
    image = wtforms.FileField()

class UserInfoForm(FlaskForm):
    username = wtforms.StringField(validators=[Length(min=3, max=20, message="用户名格式错误!(用户名应为3~20位)")])
    gender = wtforms.StringField(validators=[Optional()])
    age = wtforms.IntegerField(validators=[Optional()])
    birth_date = DateField(validators=[Optional()], format='%Y-%m-%d')
    old_password = wtforms.PasswordField()
    new_password = wtforms.StringField(validators=[Length(min=6, max=20, message="密码格式错误!(密码最少位6位)")])
    confirm_new_password = wtforms.StringField(validators=[EqualTo("new_password", message="两次密码不一致!")])
    avatar = wtforms.FileField()


class CommentForm(FlaskForm):
    content = wtforms.StringField(validators=[Length(min=1, message="内容格式错误!")])
    question_id = wtforms.IntegerField(validators=[InputRequired(message="必须要传入问题ID!")])
    parent_id = wtforms.IntegerField(validators=[], default=None)
    image = wtforms.FileField()
    

class ForgotPasswordForm(FlaskForm):
    email = wtforms.StringField(validators=[Email(message="邮箱格式错误!")])
    captcha = wtforms.StringField(validators=[Length(min=4,max=4,message="验证码格式错误!")])
    
    def validate_email(self,field):
        email = field.data
        user = UserModel.query.filter_by(email=email).first()
        if not user:
            raise wtforms.ValidationError(message="该邮箱未注册!")
    
    def validate_captcha(self,field):
        captcha = field.data
        email = self.email.data
        captcha_model = EmailCaptchaModel.query.filter_by(email=email,captcha=captcha).first()
        if not captcha_model:
            raise wtforms.ValidationError(message="邮箱或验证码错误!")
        
        now = datetime.now()
        if now - captcha_model.create_time > timedelta(minutes=5):
            raise wtforms.ValidationError(message="验证码已过期，请重新获取!")

class ResetPasswordForm(FlaskForm):
    new_password = wtforms.StringField(validators=[Length(min=6,max=20,message="密码格式错误!(密码最少位6位)")])
    confirm_new_password = wtforms.StringField(validators=[EqualTo("new_password",message="两次密码不一致!")])