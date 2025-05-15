
SECRET_KEY = "13zhiai1ren"

#数据库的配置信息
host = "127.0.0.1"
port = 3306
username = "root"
password = "root"
database = "practice"
DB_URI = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8"
SQLALCHEMY_DATABASE_URI = DB_URI

#邮箱配置
MAIL_SERVER = 'smtp.qq.com'
MAIL_USE_SSL = True
MAIL_PORT = 465
MAIL_USERNAME = '1667877328@qq.com'
MAIL_PASSWORD = 'kasgfatbolmkcbid'
MAIL_DEFAULT_SENDER = '1667877328@qq.com'