#coding: utf-8
import os
from datetime import datetime
import time
import base64
from functools import wraps
from .models import User, Article, Tag
from . import app
from . import db
from flask import jsonify
from flask import request
from flask import g
from sqlalchemy import desc
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from itsdangerous import BadSignature
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug import secure_filename

def tokenAuth(fn):
	@wraps(fn)
	def decorator(*args, **kw):
		if request.method == "GET":
			return fn(*args, **kw)
		if request.headers.get("Access-Token"):
			s = Serializer(secret_key=app.config["SECRET_KEY"],
				salt=app.config["AUTH_SALT"])
			try:
				data = s.loads(request.headers.get("Access-Token", ""))
			except SignatureExpired:
				return jsonify({'error': 'token_expired', "message": 'token is expired'})
			except BadSignature,e:
				return jsonify({'error': 'token_error', "message": 'token is invalid'})
			except:
				return jsonify({'error': 'unknown', "message": 'unknown error'})
			# 解析 token
			if 'user_id' in data:
				g.user_id = data["user_id"]
				return fn(*args, **kw)
			else:
				return jsonify({"error": "token_error", "message": 'token is invalid'})
		else:
			return jsonify({'error': 'not_login', 'message': 'miss Access-Token'})
	return decorator

@app.route("/api/auth", methods=["POST"])
def get_token():
	name = request.json.get("name")
	passwd = request.json.get("password")[:-3]
	user = User.query.filter_by(name=name).first()
	if user is None:
		return jsonify({'error': 'user_not_exist', 'message': "the user don't exists"})
	if not check_password_hash(user.passwd, passwd):
		return jsonify({"error": 'passwd_error', 'message': "password isn't correct"})
	today = str(datetime.now().day).rjust(2, '0')
	passwd_day = request.json.get("password")[-2:]
	if today != passwd_day:
		return jsonify({'error': 'passwd_format_error', 'message': 'password not match secret formmat'})
	# 根据请求的name, passwd 查询user, c传递user_id, 保存到token中
	s = Serializer(secret_key=app.config["SECRET_KEY"],
		salt=app.config["AUTH_SALT"],
		expires_in=app.config["TOKEN_EXPIRES_IN"])
	token = s.dumps({"user_id": user.id})
	return jsonify({'result': token})

@app.route("/api/upload", methods=["POST"])
@tokenAuth
def upload_file():
	title = request.args["title"]
	article_file = request.files["file"]
	article_root = app.config["FILE_ROOT_PATH"]
	b64_title = base64.b64encode(title.encode('utf-8'))
	# print b64_title, "b64_title"
	article_name = secure_filename(b64_title + ".md")
	file_path = os.path.join(article_root, article_name)
	article_file.save(file_path)
	return jsonify({'result': article_name})

@app.route("/api/articles", methods=["GET", "POST"])
@tokenAuth
def handle_articles():
	if request.method == "GET":
		return get_articles()
	elif request.method == "POST":
		return create_article()

def get_articles():
	title = request.args.get("title", "")
	skip = request.args.get("cursor", 0)
	limit = request.args.get("limit", 10)
	verbose = request.args.get("verbose", 10)
	start_time = request.args.get("startTime", 0)
	end_time = request.args.get("endTime", 0)
	query = Article.query.order_by(desc(Article.create_time))
	if start_time and end_time:
		if end_time > start_time:
			query = query.filter(Article.create_time >= start_time)\
				.filter(Article.create_time <= end_time)
		else:
			return jsonify({'error': 'param_error', 
				'message': 'request param (startTime and endTime) invalid'})
	if title != "":
		query = query.filter(Article.title.like("%"+title+"%"))
	total = query.count()
	articles = query.offset(skip).limit(limit).all()
	return jsonify({
		"total": total,
		"limit": limit,
		"cursor": skip,
		"result": [article.verbose(verbose) for article in articles]
		})

def create_article():
	title = request.json.get("title")
	summary = request.json.get("summary")
	if not (title and summary):
		return jsonify({'error': 'param_error', 'message': 'request param error'})
	tags = request.json.get('tags')
	if Article.query.filter_by(title=title).first():
		return jsonify({'error': 'resouce existed', "message": 'article title is existed'})
	now = int(time.time())
	# import random
	# now = 1520956800-random.randint(10000, 20000)
	article = Article(title=title, summary=summary, create_time=now, update_time=now)
	for tag_id in tags:
		tag = Tag.query.get(tag_id)
		if tag:
			article.tags.append(tag)
	db.session.add(article)
	db.session.commit()
	return jsonify({'result': article.serialize})

@app.route("/api/articles/<int:article_id>", methods=["GET", "DELETE", "PUT"])
@tokenAuth
def handle_article(article_id):
	article = Article.query.get(article_id)
	if not article:
		return jsonify({
			"error": 'resource_not_exist',
			"message": "resource not found"
			})
	if request.method == "GET":
		return read_article(article)
	elif request.method == "DELETE":
		return delete_article(article)
	elif request.method == "PUT":
		return update_article(article)

	
def update_article(article):
	# title = request.json.get("title")
	summary = request.json.get("summary")
	if not summary:
		return jsonify({'error': 'param_error', 'message': 'request param error'})
	article.summary = summary
	tags = request.json.get('tags')
	
	now = int(time.time())
	# article = Article(title=title, summary=summary, create_time=now, update_time=now)
	tag_list = []
	for tag_id in tags:
		tag = Tag.query.get(tag_id)
		if tag:
			tag_list.append(tag)
			# article.tags.append(tag)
	article.tags = tag_list
	# db.session.add(article)
	db.session.commit()
	return jsonify({'result': article.serialize})

def read_article(article):
	b64_name = base64.b64encode(article.title.encode("utf-8"))
	file_path = os.path.join(app.config["FILE_ROOT_PATH"], secure_filename(b64_name)+".md")
	with open(file_path, "rb") as f:
		content = f.read()
	return jsonify({'result': content})

def delete_article(article):
	db.session.delete(article)
	db.session.commit()
	file_path = os.path.join(app.config["FILE_ROOT_PATH"], article.title+".md")
	if os.path.exists(file_path):
		os.remove(file_path)
	return jsonify({'result': article.serialize})


@app.route("/api/tags", methods=["GET", "POST"])
@tokenAuth
def handle_tags():
	if request.method == "GET":
		return get_tags()
	elif request.method == 'POST':
		return create_tag()

def get_tags():
	name = request.args.get("name", "")
	skip = request.args.get("cursor", 0)
	limit = request.args.get("limit", 10)
	verbose = request.args.get("verbose", 10)
	query = Tag.query
	if name != "":
		query = Tag.query.filter(Tag.name.like("%"+name+"%"))
	total = query.count()
	if int(limit) == 0:
		tags = query.offset(skip).all() 
	else:
		tags = query.offset(skip).limit(limit).all()
	print 'tags--------',tags
	for tt in tags:
		print tt.serialize,
	return jsonify({
		"total": total,
		"limit": limit,
		"cursor": skip,
		"result": [t.verbose(verbose) for t in tags]
		})

def create_tag():
	name = request.json.get('name')
	now = int(time.time())
	tag = Tag(name=name, create_time=now, update_time=now)
	db.session.add(tag)
	db.session.commit()
	return jsonify({'result': tag.serialize})

@app.route("/api/tags/<int:tag_id>", methods=['PUT', 'DELETE'])
@tokenAuth
def handle_tag(tag_id):
	tag = Tag.query.get(tag_id)
	if not tag:
		return jsonify({
			"error": 'resource_not_exist',
			"message": "resource not found"
			})
	if request.method == "PUT":
		return update_tag(tag)
	elif request.method == "DELETE":
		return delete_tag(tag)

def update_tag(tag):
	name = request.json.get('name')
	if not name:
		return jsonify({'error': 'param_error', 'message': 'request param error'})
	tag.name = name
	tag.update_time = int(time.time())
	db.session.commit()
	return jsonify({'result': tag.serialize})

def delete_tag(tag):
	db.session.delete(tag)
	db.session.commit()
	return jsonify({'result': tag.serialize})

@app.route("/api/users", methods=["POST", "PUT"])
def create_user():
	p = '593bbd2b2780acdcb9953862898efcb7'
	hash_passwd = generate_password_hash(p, salt_length=12)
	if request.method == "POST":
		user = User(name = 'wucd', passwd=hash_passwd)
		db.session.add(user)
		db.session.commit()
		return jsonify({'result': 'add ok'})
	elif request.method == "PUT":	
		User.query.filter(User.name=="wucd").update({'passwd': hash_passwd})
		return jsonify({'result': 'update ok'})
