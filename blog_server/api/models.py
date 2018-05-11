#coding:utf-8
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.collections import InstrumentedList

db = SQLAlchemy()

class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(32), index=True)
	passwd = db.Column(db.String(128))

	def __repr__(self):
		return "User (%s): %s" % (self.id, self.name)

# ForeignKey 中使用articles( tablename),而非className
article_tag_map = db.Table("article_tag_map",
	db.Column('article_id', db.Integer, db.ForeignKey("articles.id"), primary_key=True),
	db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True))

class Article(db.Model):
	__tablename__ = "articles"
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), index=True)
	summary = db.Column(db.Text)
	create_time = db.Column(db.Integer)
	update_time = db.Column(db.Integer)
	tags = db.relationship("Tag", secondary=article_tag_map, lazy="subquery",
		backref=db.backref("articles", lazy=True))

	def __repr__(self):
		return "Article (%s): %s" % (self.id, self.title)

	@property
	def serialize(self):
		return {
			"id": self.id,
			"title": self.title,
			"create_time": self.create_time,
			"summary": self.summary,
		}

	def verbose(self, verbose_level):
		level = int(verbose_level)
		verbose_map = {'id': 10, 
			'title': 20, 
			'create_time': 30, 
			'summary': 40, 
			'update_time': 50,
			'tags': 100}
		result = {}
		for k,v in verbose_map.items():
			if v <= level:
				col_vals = getattr(self, k)
				if isinstance(col_vals, InstrumentedList):
					result[k] = [col_val.serialize for col_val in col_vals]
				else:
					result[k] = col_vals
		return result


class Tag(db.Model):
	__tablename__ = "tags"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(16), index=True)
	create_time = db.Column(db.Integer)
	update_time = db.Column(db.Integer)

	def __repr__(self):
		return "Tag (%s): %s" % (self.id, self.name)

	@property
	def serialize(self):
		return {
			"id": self.id,
			"name": self.name,
			"create_time": self.create_time
		}
	def verbose(self, verbose_level):
		level = int(verbose_level)
		verbose_map = {'id': 10, 
			'name': 20, 
			'create_time': 30, 
			'update_time': 40, 
			'articles': 100}
		result = {}
		for k,v in verbose_map.items():
			if v <= level:
				col_vals = getattr(self, k)
				if isinstance(col_vals, InstrumentedList):
					result[k] = [col_val.serialize for col_val in col_vals]
				else:
					result[k] = col_vals
		return result

# class Binding(db.Model):
# 	__tablename__ = "bindings"
# 	id = db.Column(db.Integer, primary_key=True)
# 	binding_type = db.Column(db.Integer)
# 	source = db.Column()