#coding: utf-8
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["FILE_ROOT_PATH"] = "F:/workspace/blogSite/src/articles"
# app.config['FILE_ROOT_PATH'] = "D:/gitHub/blogSite/src/articles"
app.config['SECRET_KEY'] = 'obj_id__5462cdf80ddf1a071485d85e_this_is_a_key_90'
app.config['AUTH_SALT'] = "a_auth_salt_4_1_7"
app.config["TOKEN_EXPIRES_IN"] = 30*60*10
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

import views

if not os.path.exists("db.sqlite"):
	db.create_all()