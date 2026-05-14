import re
from flask_login import login_user, logout_user

from errors import MyCamError
from repositories.user_repository import UserRepository

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    @staticmethod
    def register(email: str, password: str, nickname: str = ""):
        email = (email or "").strip().lower()
        if not _EMAIL.match(email):
            raise MyCamError("BAD_EMAIL", "Email Invalid format", 400)
        if not password or len(password) < 6:
            raise MyCamError("WEAK_PASSWORD", "Password must be at least 6 characters", 400)
        if UserRepository.get_by_email(email):
            raise MyCamError("EMAIL_TAKEN", "Email Already registered", 400)
        user = UserRepository.create(email, password, (nickname or "").strip())
        login_user(user)
        return user

    @staticmethod
    def login(email: str, password: str, remember: bool = True):
        email = (email or "").strip().lower()
        user = UserRepository.get_by_email(email)
        if not user or not user.check_password(password or ""):
            raise MyCamError("BAD_CREDENTIALS", "Wrong email or password", 401)
        login_user(user, remember=remember)
        return user

    @staticmethod
    def logout():
        logout_user()
