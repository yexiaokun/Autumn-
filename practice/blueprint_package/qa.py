from flask import Blueprint,render_template,request,g,redirect,url_for,jsonify
from .forms import QuestionForm,AnswerForm,SecondAnswerForm
from models import QuestionModel,AnswerModel,SecondAnswerModel,LikeModel
from exts import db
from decorators import login_required
from sqlalchemy import or_
from flask_sqlalchemy import pagination
import os
from werkzeug.utils import secure_filename

bp = Blueprint("qa",__name__,url_prefix="/")


#http://127.0.0.1:5000
@bp.route('/')
def index():
    #获取当前页码，默认为1
    page = request.args.get('page',1,type=int)
    #每一页显示的记录数（10条）
    per_page = 10
    
    questions_pagination = QuestionModel.query.order_by(QuestionModel.create_time.desc()).paginate(page=page,per_page=per_page,error_out=False)
    questions = questions_pagination.items
    return render_template("index.html",questions=questions,pagination=questions_pagination)


@bp.route("/qa/public_question", methods=['GET', 'POST'])
@login_required
def public_question():
    if request.method == 'GET':
        return render_template("public_question.html")
    else:
        form = QuestionForm(request.form)
        print('表单接受信息：',request.form)
        if form.validate():
            title = form.title.data
            # 接收富文本内容
            content = request.form.get('content')
            image = request.files.get('image')
            question = QuestionModel(title=title, content=content, author=g.user)

            if image:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                upload_dir = os.path.join(base_dir, '../uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                filename = secure_filename(image.filename)
                image.save(os.path.join(upload_dir, filename))
                question.image = filename

            db.session.add(question)
            db.session.commit()
            return redirect("/")
        else:
            print('表单验证错误信息:',form.errors)
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}:{error}")
            error = "<br>".join(error_messages)
            return render_template("public_question.html", error=error)


#问答详情页
@bp.route("/qa/detail/<qa_id>")
def qa_detail(qa_id):
    question = QuestionModel.query.get(qa_id)
    return render_template("detail.html",question=question)

#评论
#@bp.route("/answer/public",methods=['post'])
@bp.post("/answer/public")
@login_required
def public_answer():
    form = AnswerForm(request.form)
    if form.validate():
        # 接收富文本内容
        content = request.form.get('content')
        question_id = form.question_id.data
        image = request.files.get('image')
        answer = AnswerModel(content=content, question_id=question_id, author_id=g.user.id)

        if image:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            upload_dir = os.path.join(base_dir, '../uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            filename = secure_filename(image.filename)
            image.save(os.path.join(upload_dir, filename))
            answer.image = filename

        db.session.add(answer)
        db.session.commit()
        return redirect(url_for("qa.qa_detail", qa_id=question_id))
    else:
        print(form.errors)
        return redirect(url_for("qa.qa_detail", qa_id=request.form.get("question_id")))

#搜索
@bp.route("/search")
def search():
    #/search?q=flask
    #/search/<q>
    #post,request.form
    q = request.args.get("q")
    page = request.args.get('page',1,type=int)
    per_page = 10
    questions_pagination = QuestionModel.query.filter(
        or_(QuestionModel.title.contains(q),QuestionModel.content.contains(q),QuestionModel.author.has(username=q))
        ).order_by(QuestionModel.create_time.desc()).paginate(page=page,per_page=per_page,error_out=False)
    questions = questions_pagination.items
    no_results = len(questions) == 0 #判断是否没有搜索结果
    return render_template("index.html",questions=questions,pagination=questions_pagination,no_results=no_results,q=q)

#删除评论
@bp.route("/delete_answer/<int:answer_id>",methods=['POST'])
@login_required
def delete_answer(answer_id):
    answer = AnswerModel.query.get(answer_id)
    if answer and answer.author == g.user:
        question_id = answer.question_id
        db.session.delete(answer)
        db.session.commit()
        return redirect(url_for('qa.qa_detail',qa_id = question_id))
    return redirect(url_for('qa.qa_detail',qa_id = answer.question_id)) if answer else redirect(url_for('qa.index'))

#二级评论
@bp.route("/second_answer/public",methods=['POST'])
@login_required
def public_second_answer():
    print(f"Request method: {request.method}")
    print(f"Request data: {request.form}")
    form = SecondAnswerForm(request.form)
    if form.validate():
        content = form.content.data
        answer_id = form.answer_id.data
        image = request.files.get('image')
        second_answer = SecondAnswerModel(content = content,answer_id = answer_id,author_id = g.user.id,image=image)
        if image:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            upload_dir = os.path.join(base_dir,'../uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            filename = secure_filename(image.filename)
            image.save(os.path.join(upload_dir,filename))
            second_answer.image = filename
            
        db.session.add(second_answer)
        db.session.commit()
        answer = AnswerModel.query.get(answer_id)
        return redirect(url_for('qa.qa_detail',qa_id = answer.question_id))
    else:
        print(form.errors)
        answer = AnswerModel.query.get(request.form.get("answer_id"))
        return redirect(url_for('qa.qa_detail',qa_id = answer.question_id))

#删除二级评论
@bp.route("/delete_second_answer/<int:second_answer_id>", methods=['POST'])
@login_required
def delete_second_answer(second_answer_id):
    second_answer = db.session.get(SecondAnswerModel,second_answer_id)
    if second_answer and second_answer.author == g.user:
        answer = second_answer.answer
        db.session.delete(second_answer)
        db.session.commit()
        return redirect(url_for('qa.qa_detail', qa_id=answer.question_id))
    return redirect(url_for('qa.qa_detail', qa_id=answer.question_id)) if answer else redirect(url_for('qa.index'))

@bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    image = request.files.get('image')
    if image:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, '../uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        filename = secure_filename(image.filename)
        image.save(os.path.join(upload_dir, filename))
        url = url_for('uploaded_file', filename=filename)
        return jsonify({'success': True, 'url': url})
    return jsonify({'success': False})

#点赞问答
@bp.route('/like_question/<int:question_id>', methods=['POST'])
@login_required
def like_question(question_id):
    question = QuestionModel.query.get(question_id)
    if question:
        like = LikeModel.query.filter_by(user_id=g.user.id, question_id=question_id).first()
        if like:
            # 取消点赞
            db.session.delete(like)
            question.likes = question.likes - 1 if question.likes > 0 else 0
        else:
            # 点赞
            new_like = LikeModel(user_id=g.user.id, question_id=question_id)
            db.session.add(new_like)
            question.likes = question.likes + 1 if question.likes is not None else 1
        db.session.commit()
        return jsonify({'success': True, 'likes': question.likes})
    return jsonify({'success': False})

# 点赞评论
@bp.route('/like_answer/<int:answer_id>', methods=['POST'])
@login_required
def like_answer(answer_id):
    answer = AnswerModel.query.get(answer_id)
    if answer:
        like = LikeModel.query.filter_by(user_id=g.user.id, answer_id=answer_id).first()
        if like:
            # 取消点赞
            db.session.delete(like)
            answer.likes = answer.likes - 1 if answer.likes > 0 else 0
        else:
            # 点赞
            new_like = LikeModel(user_id=g.user.id, answer_id=answer_id)
            db.session.add(new_like)
            answer.likes = answer.likes + 1 if answer.likes is not None else 1
        db.session.commit()
        return jsonify({'success': True, 'likes': answer.likes})
    return jsonify({'success': False})

# 点赞二级评论
@bp.route('/like_second_answer/<int:second_answer_id>', methods=['POST'])
@login_required
def like_second_answer(second_answer_id):
    second_answer = SecondAnswerModel.query.get(second_answer_id)
    if second_answer:
        like = LikeModel.query.filter_by(user_id=g.user.id, second_answer_id=second_answer_id).first()
        if like:
            # 取消点赞
            db.session.delete(like)
            second_answer.likes = second_answer.likes - 1 if second_answer.likes > 0 else 0
        else:
            # 点赞
            new_like = LikeModel(user_id=g.user.id, second_answer_id=second_answer_id)
            db.session.add(new_like)
            second_answer.likes = second_answer.likes + 1 if second_answer.likes is not None else 1
        db.session.commit()
        return jsonify({'success': True, 'likes': second_answer.likes})
    return jsonify({'success': False})

#url传参
#邮件发送
#ajax
#orm与数据库
#jinja2
#cookie和session原理
#搜索