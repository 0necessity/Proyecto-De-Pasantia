import base64
import html
from flask import *  # fix this later
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .auth import SignUp

engine = create_engine("sqlite:///mydb.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()
views = Blueprint("views", __name__)


def log_check():
    cookie = request.cookies
    user_cookie = cookie.get("user")
    menu_items = []

    if user_cookie is not None:
        user = session.query(SignUp).filter_by(cookieid=user_cookie).first()
        if user is not None:
            encoded_image = base64.b64encode(user.photo).decode('utf-8')
            named = html.escape(user.name)

            menu_items = [
                f'<a class="nav-item nav-link" id="logout" href="/logout">Logout</a>',
                f"""
                <link rel="stylesheet" href="../static/please.css">
                <a href="/profile" class="link">
                    <p><span style="color: white;">Hola, {named}</span></p>
                    <img src="data:image/png;base64,{encoded_image}" class="rounded-circle me-2 ms-auto">
                </a>
                """
            ]
    return menu_items


@views.route('/', methods=['GET', 'POST'])
def home():

    # s = session.query(SignUp).filter(SignUp.emails == "luisjaviercg9@gmail.com").first()
    res = make_response(render_template("front.html", code=log_check()))
    return res

