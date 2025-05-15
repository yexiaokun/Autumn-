from flask import Blueprint,render_template,request,g,redirect,url_for,jsonify,abort
from .forms import QuestionForm,CommentForm
from models import QuestionModel,LikeModel,CommentModel,UserModel,FollowModel
from exts import db
from decorators import login_required
from sqlalchemy import or_
from flask_sqlalchemy import pagination
import os
from werkzeug.utils import secure_filename

bp = Blueprint("qa",__name__,url_prefix="/")


# http://127.0.0.1:5000
@bp.route('/')
def index():
    # 获取当前页码，默认为1
    page = request.args.get('page', 1, type=int)
    per_page = 10
    tab = request.args.get('tab', 'hot')  # 默认显示“热门”内容

    if tab == 'following' and g.user:
        # 查询关注的用户发表的文章
        following_users = [follow.followed_id for follow in FollowModel.query.filter_by(follower_id=g.user.id).all()]
        questions_pagination = QuestionModel.query.filter(
            QuestionModel.author_id.in_(following_users)
        ).order_by(QuestionModel.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        # 默认显示热门内容
        questions_pagination = QuestionModel.query.order_by(QuestionModel.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)

    questions = questions_pagination.items

    # 获取点赞信息
    liked_question_ids = []
    liked_comment_ids = []
    if g.user:
        liked_question_ids = [like.question_id for like in LikeModel.query.filter_by(user_id=g.user.id).all()]
        liked_comment_ids = [like.comment_id for like in LikeModel.query.filter_by(user_id=g.user.id).all()]

    # 构建每个问题的一级评论和其对应的回复
    question_comments = {}
    for question in questions:
        # 只获取一级评论（parent_id=None）
        first_level_comments = CommentModel.query.filter_by(
            question_id=question.id,
            parent_id=None
        ).order_by(CommentModel.create_time.asc()).all()

        # 给每个一级评论绑定它的子回复
        for comment in first_level_comments:
            comment.second_comments = CommentModel.query.filter_by(
                parent_id=comment.id
            ).order_by(CommentModel.create_time.asc()).all()

        question_comments[question.id] = first_level_comments

    form = CommentForm()

    return render_template("index.html",
                            questions=questions,
                            pagination=questions_pagination,
                            liked_question_ids=liked_question_ids,
                            liked_comment_ids=liked_comment_ids,
                            question_comments=question_comments,
                            form=form,
                            tab=tab)

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
                    error_messages.append(f"{error}")
            error = "<br>".join(error_messages)
            return render_template("public_question.html", error=error,form=form)


#问答详情页
@bp.route("/qa/detail/<int:qa_id>")
def qa_detail(qa_id):
    question = QuestionModel.query.get(qa_id)
    if not question:
        abort(404)
    
    first_level_comments = CommentModel.query.filter_by(question_id=qa_id, parent_id=None).order_by(CommentModel.create_time.asc()).all()
    for comment in first_level_comments:
        comment.second_comments = CommentModel.query.filter_by(parent_id=comment.id).order_by(CommentModel.create_time.asc()).all()
    question.comments = first_level_comments
    
    
    liked_question_ids = []
    liked_comment_ids = []
    if g.user:
        liked_question_ids = [like.question_id for like in LikeModel.query.filter_by(user_id=g.user.id).all()]
        liked_comment_ids = [like.comment_id for like in LikeModel.query.filter_by(user_id=g.user.id).all()]
    form = CommentForm()
    return render_template("detail.html", question=question, liked_question_ids=liked_question_ids,
                            liked_comment_ids=liked_comment_ids,form=form)
#评论
#@bp.route("/comment/public",methods=['post'])
@bp.post("/comment/public")
@login_required
def public_comment():
    form = CommentForm(request.form)
    if form.validate():
        # 接收富文本内容
        content = request.form.get('content')
        question_id = form.question_id.data
        parent_id = form.parent_id.data
        image = request.files.get('image')
        comment = CommentModel(content=content, question_id=question_id, author_id=g.user.id, parent_id=parent_id)

        if image:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            upload_dir = os.path.join(base_dir, '../uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            filename = secure_filename(image.filename)
            image.save(os.path.join(upload_dir, filename))
            comment.image = filename

        try:
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("qa.qa_detail", qa_id=question_id))
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
            # 从 request.form 中获取 question_id
            question_id = request.form.get("question_id")
            return redirect(url_for("qa.qa_detail", qa_id=question_id))
    else:
        print(form.errors)
        question_id = request.form.get("question_id")
        return redirect(url_for("qa.qa_detail", qa_id=question_id))

@bp.post("/public_second_comment")
@login_required
def public_second_comment():
    form = CommentForm(request.form)
    if form.validate():
        # 获取表单中的内容
        content = request.form.get('content').strip()

        # 检查内容是否为空
        if not content or content == '<p><br></p>':
            print("Received empty content")
            return redirect(request.referrer or url_for("qa.index"))

        question_id = form.question_id.data
        parent_id = form.parent_id.data

        # 创建评论对象
        comment = CommentModel(content=content, question_id=question_id, author_id=g.user.id, parent_id=parent_id)

        db.session.add(comment)
        db.session.commit()

        # 如果请求来自首页，返回首页
        if request.referrer and 'index' in request.referrer:
            return redirect(url_for("qa.index", tab="hot"))

        # 默认返回问答详情页
        return redirect(url_for("qa.qa_detail", qa_id=question_id))
    else:
        print("Form validation errors:", form.errors)
        return redirect(request.referrer or url_for("qa.index"))

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
    form = CommentForm()
    return render_template("index.html",questions=questions,pagination=questions_pagination,no_results=no_results,q=q,form=form)

#删除评论
@bp.route("/delete_comment/<int:comment_id>",methods=['delete'])
@login_required
def delete_comment(comment_id):
    comment = CommentModel.query.get(comment_id)
    if comment and comment.author == g.user:
        question_id = comment.question_id
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"success": True, "message": "回复已删除"})
    return jsonify({"success": False, "message": "无权限删除或回复不存在"})

#删除二级评论
@bp.route("/delete_second_comment/<int:second_comment_id>", methods=['POST'])
@login_required
def delete_second_comment(second_comment_id):
    comment = CommentModel.query.get(second_comment_id)
    if comment and comment.author == g.user:
        question_id = comment.question_id
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"success": True, "message": "评论已删除"})
    return jsonify({"success": False, "message": "无权限删除或评论不存在"})

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
@bp.route('/like_question', methods=['POST'])
@login_required
def like_question():
    question_id = request.json.get('question_id')
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
@bp.route('/like_comment/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = CommentModel.query.get(comment_id)
    if comment:
        like = LikeModel.query.filter_by(user_id=g.user.id, comment_id=comment_id).first()
        if like:
            # 取消点赞
            db.session.delete(like)
            comment.likes = comment.likes - 1 if comment.likes > 0 else 0
        else:
            # 点赞
            new_like = LikeModel(user_id=g.user.id, comment_id=comment_id)
            db.session.add(new_like)
            comment.likes = comment.likes + 1 if comment.likes is not None else 1
        db.session.commit()
        return jsonify({'success': True, 'likes': comment.likes})
    return jsonify({'success': False})

# 点赞二级评论
@bp.route('/like_second_comment', methods=['PUT'])
@login_required
def like_second_comment():
    second_comment_id = request.json.get('second_comment_id')
    print("二级评论ID:", second_comment_id)
    second_comment = CommentModel.query.get(second_comment_id)
    if second_comment:
        like = LikeModel.query.filter_by(user_id=g.user.id, comment_id=second_comment_id).first()
        if like:
            # 取消点赞
            db.session.delete(like)
            second_comment.likes = second_comment.likes - 1 if second_comment.likes > 0 else 0
        else:
            # 点赞
            new_like = LikeModel(user_id=g.user.id, comment_id=second_comment_id)
            db.session.add(new_like)
            second_comment.likes = second_comment.likes + 1 if second_comment.likes is not None else 1
        db.session.commit()
        return jsonify({'success': True, 'likes': second_comment.likes})
    return jsonify({'success': False})

#点赞问题的人
@bp.route('/question_likers/<int:question_id>', methods=['GET'])
@login_required
def question_likers(question_id):

    question = QuestionModel.query.get(question_id)
    if question:
        likers = [like.user for like in question.likes_users]
        liker_info = [{'id': liker.id, 'username': liker.username} for liker in likers]
        return jsonify({'success': True, 'likers': liker_info})
    return jsonify({'success': False})
    
#点赞评论的人
@bp.route('/comment_likers/<int:comment_id>', methods=['GET'])
@login_required
def comment_likers(comment_id):

    comment = CommentModel.query.get(comment_id)
    if comment:
        likers = [like.user for like in comment.likes_users]
        liker_info = [{'id': liker.id, 'username': liker.username} for liker in likers]
        return jsonify({'success': True, 'likers': liker_info})
    return jsonify({'success': False})
    
    
#点赞二级评论的人
@bp.route('/second_comment_likers/<int:second_comment_id>', methods=['GET'])
@login_required
def second_comment_likers(second_comment_id):
    
    second_comment = CommentModel.query.get(second_comment_id)
    if second_comment:
        likers = [like.user for like in second_comment.likes_users]
        liker_info = [{'id': liker.id, 'username': liker.username} for liker in likers]
        return jsonify({'success': True, 'likers': liker_info})
    return jsonify({'success': False})
    
    
#url传参
#邮件发送
#ajax
#orm与数据库
#jinja2
#cookie和session原理
#搜索