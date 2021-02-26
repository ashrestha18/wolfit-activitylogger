from datetime import datetime
from flask import flash, redirect, render_template, request, url_for, jsonify, abort
from flask_login import current_user, login_required, login_user, logout_user
from app import app, db
from app.forms import CommentForm, LoginForm, PostForm, RegistrationForm
from app.models import ActivityLog, Category, Comment, Post, User
from mongoengine import connect
import json
import requests
from bson.objectid import ObjectId
import pymongo

client = pymongo.MongoClient("mongodb+srv://root:root@cluster0.tltap.mongodb.net/ActivityLog?retryWrites=true&w=majority")
logs = client.ActivityLog.logs

@app.route('/api/activities/', methods=["GET"])
def list_of_activity():
    json_logs = []
    count = 0
    for log in logs.find().sort("timestamp",pymongo.DESCENDING):
        if count ==10:
            break
        log['_id']=str(log['_id'])
        json_logs.append(log)
        count = count + 1
    print(json_logs)
    return jsonify({'activities': json_logs})


@app.route('/api/activities', methods=["POST"])
def post_activity():
    print(request)
    if not request.json:
        abort(400)
    new_activity = request.get_json()
    if ('user_id' not in new_activity or 'username' not in new_activity or 'details' not in new_activity):
        abort(400)
    new_log = {
        'user_id':new_activity['user_id'],
        'username':new_activity['username'],
        'timestamp':datetime.utcnow(),
        'details':new_activity['details']}
    logs.insert_one(new_log)
    return new_activity, 201

@app.route('/api/activities/<string:str_id>', methods=["GET"])
def  get_activity(str_id):
    if ObjectId.is_valid(str_id):
        log = None
        for l in logs.find():
            if str(l['_id'])==str_id:
                log = l
                log['_id']=str(log['_id'])
                break

        if log is None:
            abort(404)
        log["_id"]=str(log["_id"])
    else:
        abort(404)

    return jsonify(log)


def greeting_name():
    greeting_name = "Anonymous"
    if current_user.is_authenticated:
        greeting_name = current_user.username
    return greeting_name


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@app.route("/")
@app.route("/index")
def index():
    page = request.args.get("page", 1, type=int)
    posts = Post.recent_posts().paginate(page, app.config["POSTS_PER_PAGE"], False)

    return render_template(
        "index.html",
        title="The Front Page of WOU",
        greeting_name=greeting_name(),
        posts=posts,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        myobj = {'user_id': user.id,'username': user.username,'details': f"Login {user}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        # ActivityLog.log_event(user.id, f"Login {user}")
        return redirect(url_for("index"))
    elif form.is_submitted():
        return redirect(url_for("login"))
    else:
        return render_template(
            "login.html", greeting_name=greeting_name(), title="Login", form=form
        )


@app.route("/logout")
def logout():
    # ActivityLog.log_event(current_user.id, f"Logout {current_user}")
    myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Logout {current_user}"}
    x = requests.post(request.url_root+'api/activities', json = myobj)
    logout_user()
    return redirect(url_for("index"))


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if not current_user.is_authenticated:
        return redirect(url_for("register"))

    category_id = request.args.get("category_id", None, type=int)
    form = PostForm()
    categories = Category.query.order_by("title")
    if categories.count() == 0:
        category = Category(title="default")
        db.session.add(category)
        db.session.commit()
        categories = Category.query.order_by("title")
    form.category_id.choices = [
        (c.id, c.title) for c in categories
    ]
    form.category_id.data = category_id or categories.first().id

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            body=form.body.data,
            link=form.link.data,
            url=form.url.data,
            category_id=form.category_id.data,
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        # ActivityLog.log_event(current_user.id, f"Create: {post}")
        myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Create: {post}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        flash("Your post is now live!")
        return redirect(url_for("index"))
    return render_template(
        "create_post.html",
        greeting_name=greeting_name(),
        title="Create Post",
        form=form,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # ActivityLog.log_event(user.id, "Register")
        myobj = {'user_id': user.id,'username': user.username,'details': "Register"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template(
        "register.html", greeting_name=greeting_name(), title="Register", form=form
    )


@app.route("/user/<username>")
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.paginate(page, app.config["POSTS_PER_PAGE"], False)

    return render_template(
        "user.html",
        greeting_name=greeting_name(),
        title="Profile",
        user=user,
        posts=posts,
    )


@app.route("/w/<title>")
def category(title):
    category = Category.query.filter_by(title=title).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = category.posts.paginate(page, app.config["POSTS_PER_PAGE"], False)

    return render_template(
        "category.html",
        greeting_name=greeting_name(),
        title="Category",
        category=title,
        category_id=category.id,
        posts=posts,
    )


@app.route("/post/<post_id>", methods=["GET", "POST"])
def post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        post.add_comment(form.body.data, current_user)
        flash("Your comment is now live!")
        return redirect(url_for("post", post_id=post_id))
    return render_template(
        "post.html",
        greeting_name=greeting_name(),
        title=post.title,
        post=post,
        comments=post.comments,
        form=form,
    )


@app.route("/up_vote/<post_id>")
def up_vote(post_id):
    next_page = request.args.get("next")
    if current_user.is_authenticated:
        post = Post.query.filter_by(id=post_id).first_or_404()
        post.up_vote(current_user)
        # ActivityLog.log_event(current_user.id, f"Up Vote: {post}")
        myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Up Vote: {post}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        return redirect(next_page or url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/down_vote/<post_id>")
def down_vote(post_id):
    next_page = request.args.get("next")
    if current_user.is_authenticated:
        post = Post.query.filter_by(id=post_id).first_or_404()
        post.down_vote(current_user)
        # ActivityLog.log_event(current_user.id, f"Down Vote: {post}")
        myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Down Vote: {post}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        return redirect(next_page or url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/up_vote_comment/<comment_id>")
def up_vote_comment(comment_id):
    next_page = request.args.get("next")
    if current_user.is_authenticated:
        comment = Comment.query.filter_by(id=comment_id).first_or_404()
        comment.up_vote(current_user)
        # ActivityLog.log_event(current_user.id, f"Up Vote: {comment}")
        myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Up Vote: {comment}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        return redirect(next_page or url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/down_vote_comment/<comment_id>")
def down_vote_comment(comment_id):
    next_page = request.args.get("next")
    if current_user.is_authenticated:
        comment = Comment.query.filter_by(id=comment_id).first_or_404()
        comment.down_vote(current_user)
        # ActivityLog.log_event(current_user.id, f"Down Vote: {comment}")
        myobj = {'user_id': current_user.id,'username': current_user.username,'details': f"Down Vote: {comment}"}
        x = requests.post(request.url_root+'api/activities', json = myobj)
        return redirect(next_page or url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/shutdown", methods=["GET"])
def shutdown():
    shutdown_server()
    return "Server shutting down..."
