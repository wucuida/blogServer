#coding: utf-8
import os
from flask import Flask,request,jsonify
from .api.models import db
from werkzeug.exceptions import InternalServerError


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

def init_log(app):
	if app.debug:
		import logging
		from logging.handlers import SMTPHandler
		from logging.handlers import RotatingFileHandler
		ADMINS = app.config.get("ADMIN_EMAILS", [])
		mail_handler = SMTPHandler('127.0.0.1',
									'server-error@wucd.com',
									ADMINS, 'wucd.wang blog_server has errors!')
		mail_handler.setFormatter(logging.Formatter('''
			Message type:       %(levelname)s
			Location:           %(pathname)s:%(lineno)d
			Module:             %(module)s
			Function:           %(funcName)s
			Time:               %(asctime)s
			Message:            %(message)s
			'''))
		mail_handler.setLevel(logging.ERROR)
		app.logger.addHandler(mail_handler)
		log_home = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
		if not os.path.exists(log_home):
			os.makedirs(log_home)       
		file_handler = RotatingFileHandler(os.path.join(log_home, "server_log.log"),
			maxBytes=4*1024*1024, backupCount=10)
		file_handler.setLevel(logging.WARNING)
		file_handler.setFormatter(logging.Formatter(
				'%(levelname)s - %(asctime)s @ %(pathname)s (%(lineno)s): %(message)s '
			))
		app.logger.addHandler(file_handler)
		@app.errorhandler(InternalServerError)
		def handle_server_error(e):
			app.logger.error(e)
			app.logger.error(e.message)
			return jsonify({'error': "system_error", "message": "System internal error"})

def create_app():
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_object('blog_server.config.DefaultConfig')
	app.config.from_pyfile("config.py")
	init_db(app)
	init_log(app)
	init_app(app)   
	return app

