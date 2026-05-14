"""書籍搜尋 MVC Controller。"""
from flask import Blueprint, render_template

book_bp = Blueprint("book", __name__)


@book_bp.get("/")
def index():
    return render_template("book/index.html", active="book")
