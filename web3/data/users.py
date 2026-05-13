import datetime
import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # добавить импорт

from .db_session import SqlAlchemyBase


class User(UserMixin, SqlAlchemyBase):  # добавить UserMixin
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    habits = orm.relationship('Habit', back_populates='user')

    def __repr__(self):
        return f'<User> {self.id} {self.username}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)