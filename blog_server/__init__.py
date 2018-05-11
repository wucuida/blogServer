#coding: utf-8
import os
from flask import Flask,request
from .api.models import db


def init_db(app):
	# 模块同级目录下保存db文件
	db_home = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
	if not os.path.exists(db_home):
		os.makedirs(db_home)
	db.init_app(app)
	db_file = os.path.join(db_home, "db.sqlite")
	if not os.path.exists(db_file):				
		db.create_all()

def init_app(app):
	from api import api
	app.register_blueprint(api, url_prefix='/api')

def create_app():
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_object('blog_server.config.DefaultConfig')
	app.config.from_pyfile("config.py")
	init_db(app)
	init_app(app)	
	return app

