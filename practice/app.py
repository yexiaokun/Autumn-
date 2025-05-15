from flask import Flask,session,g,send_from_directory,request,jsonify,json
from dotenv import load_dotenv
import config
from exts import db,mail
from models import UserModel
from blueprint_package.qa import bp as qa_bp
from blueprint_package.auth import bp as auth_bp
from flask_migrate import Migrate
import os,re,requests
from flask_wtf.csrf import CSRFProtect,CSRF
from flask_cors import CORS

load_dotenv()  # 加载环境变量
app = Flask(__name__,static_folder='static')

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-CSRFToken"]
    }
})  # 允许前端访问API

#绑定配置文件
app.config.from_object(config)
app.config['PROPAGATE_EXCEPTIONS'] = True  # 显示完整错误堆栈


#会话存储配置
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

db.init_app(app)
mail.init_app(app)
csrf=CSRFProtect(app)

migrate = Migrate(app,db)


app.register_blueprint(qa_bp)
app.register_blueprint(auth_bp)

# 添加会话密钥配置
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-123")

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
    print(f'Current g.user:{g.user}')#添加调试信息
    amap_key = os.getenv("AMAP_KEY")
    return {"user":g.user,"amap_key":amap_key}


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    return send_from_directory(upload_dir, filename)


@app.template_filter('remove_images')
def remove_images(content):
    return re.sub(r"<img[^>]*>",'',content)

#嵌入AI
@csrf.exempt
@app.route('/api/chat', methods=["POST"])
def chat():
    try:
        # ======= 新增调试信息 =======
        print("\n=== 请求头信息 ===")
        print(dict(request.headers))
        
        print("\n=== 请求原始数据 ===")
        print(request.get_data(as_text=True))
        # 检查会话存储
        print("\n=== 当前会话信息 ===")
        print("User ID:", session.get("user_id"))
        print("Chat History:", session.get("chat_history"))
        print("\n=== 环境变量验证 ===")
        print("HUGGINGFACE_API_KEY exists:", bool(os.getenv("HUGGINGFACE_API_KEY")))
        # ========================
        # 校验请求格式
        if not request.json or 'messages' not in request.json:
            return jsonify({"success": False, "error": "Invalid request format"}), 400

        # 获取 API 密钥
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return jsonify({"success": False, "error": "API key not configured"}), 500

        # 构造请求
        model_id = "gpt2" #根据需求选择模型
        input_text = request.json["messages"][0]["content"]
        payload = {
            "inputs": input_text
        }

        # 发送请求
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            timeout=30
        )

        
            # 处理 API 响应
        response.raise_for_status()  # 自动抛出 HTTP 错误
        try:
            response_data = response.json()
            print("API响应数据:", response_data)  # 调试信息
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid API response"}), 500

        # 校验响应结构
        if not isinstance(response_data, list) or not response_data[0].get("generated_text"):
            return jsonify({
                "success": False,
                "error": "Invalid API response structure"
            }), 500

        return jsonify({
            "success": True,
            "response": {
                "choices": [
                    {
                        "message": {
                            "content": response_data[0]["generated_text"]
                        }
                    }
                ]
            }
        })

    except requests.exceptions.HTTPError as e:
        # 捕获 Hugging Face API 错误
        error_msg = f"API Error: {e.response.text}"
        print("HTTP错误:", error_msg)  # 调试信息
        return jsonify({"success": False, "error": error_msg}), 500
    except Exception as e:
        print("其他异常:", str(e))  # 调试信息
        # 其他异常处理
        return jsonify({"success": False, "error": str(e)}), 500

print(os.getcwd())

if __name__ == "__main__":
    app.run(debug=True)