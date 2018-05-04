#coding: utf-8
from blog_server import app

if __name__ == "__main__":
	app.run(threaded=True, debug=True)