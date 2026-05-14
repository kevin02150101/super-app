from typing import Optional
from extensions import db
from models.user import User


class UserRepository:
    @staticmethod
    def get(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return db.session.query(User).filter_by(email=email).first()

    @staticmethod
    def create(email: str, password: str, nickname: str = "") -> User:
        u = User(email=email, nickname=nickname or None)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u
