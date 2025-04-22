from flask import Flask,session,g,send_from_directory
import config
from exts import db,mail
from models import UserModel
from blueprint_package.qa import bp as qa_bp
from blueprint_package.auth import bp as auth_bp
from flask_migrate import Migrate
import os,re

app = Flask(__name__,static_folder='static')

#绑定配置文件
app.config.from_object(config)

db.init_app(app)
mail.init_app(app)

migrate = Migrate(app,db)

app.register_blueprint(qa_bp)
app.register_blueprint(auth_bp)


#before_request/before_first_request/after_request(钩子函数)
#hook
@app.before_request
def my_before_request():
    user_id = session.get("user_id")
    if user_id:
        user = db.session.get(UserModel,user_id)
        setattr(g,"user",user)
    else:
        setattr(g,"user",None)
    
    

@app.context_processor
def my_context_processor():
    return {"user":g.user}


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    return send_from_directory(upload_dir, filename)


@app.template_filter('remove_images')
def remove_images(content):
    return re.sub(r"<img[^>]*>",'',content)


print(os.getcwd())

if __name__ == "__main__":
    app.run(debug=True)