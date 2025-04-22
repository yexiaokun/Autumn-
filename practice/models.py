from exts import db
from datetime import datetime

class UserModel(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(100),nullable=False)
    password = db.Column(db.String(200),nullable=False)
    email = db.Column(db.String(100),nullable=False,unique=True)
    join_time = db.Column(db.DateTime,default=datetime.now)
    avatar = db.Column(db.String(200))
    

class EmailCaptchaModel(db.Model):
    __tablename__ = "email_captcha"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(100),nullable=False)
    captcha = db.Column(db.String(100),nullable=False)
    
    
class QuestionModel(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    title = db.Column(db.String(100),nullable=False)
    content = db.Column(db.Text,nullable=False)
    create_time = db.Column(db.DateTime,default=datetime.now)
    
    #外键
    author_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    author = db.relationship(UserModel,backref="questions")
    #后添加的image字段，用来输入图片
    image = db.Column(db.String(200))
    #点赞字段
    likes = db.Column(db.Integer, default=0)
    
class AnswerModel(db.Model):
    __tablename__ = "answer"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    content = db.Column(db.Text,nullable=False)
    create_time = db.Column(db.DateTime,default=datetime.now)
    
    #外键
    question_id = db.Column(db.Integer,db.ForeignKey("question.id"))
    author_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    
    #关系
    question = db.relationship(QuestionModel,backref=db.backref("answers",order_by=create_time.desc()))
    author = db.relationship(UserModel,backref="answers")
    #后添加的image字段，用来输入图片
    image = db.Column(db.String(200))
    #点赞字段
    likes = db.Column(db.Integer, default=0)

class SecondAnswerModel(db.Model):
    __tablename__ = "second_answer"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    image = db.Column(db.String(200))
    #点赞字段
    likes = db.Column(db.Integer, default=0)

    # 外键
    answer_id = db.Column(db.Integer, db.ForeignKey("answer.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # 关系
    answer = db.relationship(AnswerModel, backref=db.backref("second_answers", order_by=create_time.desc()))
    author = db.relationship(UserModel, backref="second_answers")
    
class LikeModel(db.Model):
    __tablename__ = "like"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))
    answer_id = db.Column(db.Integer, db.ForeignKey("answer.id"))
    second_answer_id = db.Column(db.Integer, db.ForeignKey("second_answer.id"))
    user = db.relationship(UserModel, backref="likes")
    question = db.relationship(QuestionModel, backref="likes_users")
    answer = db.relationship(AnswerModel, backref="likes_users")
    second_answer = db.relationship(SecondAnswerModel, backref="likes_users")