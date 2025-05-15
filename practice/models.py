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
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    birth_date = db.Column(db.Date)
    followers = db.relationship('FollowModel', foreign_keys='FollowModel.followed_id', backref='followed', lazy='dynamic')
    following = db.relationship('FollowModel', foreign_keys='FollowModel.follower_id', backref='follower', lazy='dynamic')
    

class EmailCaptchaModel(db.Model):
    __tablename__ = "email_captcha"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.String(100),nullable=False)
    captcha = db.Column(db.String(100),nullable=False)
    create_time = db.Column(db.DateTime,default=datetime.now)
    
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
    
class CommentModel(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    content = db.Column(db.Text,nullable=False)
    create_time = db.Column(db.DateTime,default=datetime.now)
    #后添加的image字段，用来输入图片
    image = db.Column(db.String(200))
    #点赞字段
    likes = db.Column(db.Integer, default=0)
    
    #外键
    question_id = db.Column(db.Integer,db.ForeignKey("question.id"))
    author_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    parent_id = db.Column(db.Integer,db.ForeignKey("comment.id"))
    #关系
    parent = db.relationship('CommentModel', remote_side=[id], backref='children')
    author = db.relationship('UserModel', backref='comments')
    question = db.relationship('QuestionModel', backref='comments')

    
class LikeModel(db.Model):
    __tablename__ = "like"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))
    comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"))
    user = db.relationship(UserModel, backref="likes")
    question = db.relationship(QuestionModel, backref="likes_users")
    comment = db.relationship(CommentModel,backref="likes_users")
    

class FollowModel(db.Model):
    __tablename__ = "follow"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    create_time = db.Column(db.DateTime, default=datetime.now)
