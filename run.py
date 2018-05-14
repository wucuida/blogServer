# coding: utf-8
import os
from blog_server import create_app


if __name__ == "__main__":
    # if not os.path.exists("db.sqlite"):
    # db.create_all()
    app = create_app()
    app.run()
