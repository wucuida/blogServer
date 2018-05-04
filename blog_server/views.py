#coding: utf-8
from datetime import datetime
from .models import User
from . import app
from . import db
from flask import jsonify
from flask import request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from itsdangerous import BadSignature
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

@app.route("/a")
def test():
	return jsonify({"a": 1})

def tokenAuth(fn):
	@wraps(fn)
	def decorator(*args, **kw):
		if request.headers.get("access_token"):
			s = Serializer(secret_key=app.config["SECRET_KEY"],
				salt=app.config["AUTH_SALT"])
			try:
				data = s.loads(request.headers.get("access_token", ""))
			except SignatureExpired:
				return jsonify({'error': 'token_expired', "message": 'token is expired'})
			except BadSignature,e:
				return jsonify({'error': 'token_error', "message": 'token is invalid'})
			except:
				return jsonify({'error': 'unknown', "message": 'unknown error'})
			# 解析 token
			if user_id in data:
				g.user_id = data["user_id"]
				fn(*args, **kw)
			else:
				return jsonify({"error": "token_error", "message": 'token is invalid'})
		else:
			return jsonify({'error': 'not_login', 'message': 'miss access_token'})
	return decorator

@app.route("/api/auth", methods=["POST"])
def get_token():
	name = request.json.get("name")
	print request.json.get("password")
	passwd = request.json.get("password")[:-3]
	print passwd
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
	return s.dumps({"user_id": 'user_id'})


@app.route("/api/users", methods=["POST", "PUT"])
def create_user():
	p = '593bbd2b2780acdcb9953862898efcb7'
	if request.method == "POST":
		user = User(name = 'wucd', passwd=p)
		db.session.add(user)
		db.session.commit()
		return jsonify({'ok': '1'})
	elif request.method == "PUT":
		hash_passwd = generate_password_hash(p, salt_length=12)
		User.query.filter(User.name=="wucd").update({'passwd': hash_passwd})
		return jsonify({'ok': '2'})
