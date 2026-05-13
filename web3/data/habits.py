import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Habit(SqlAlchemyBase):
    __tablename__ = 'habits'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User', back_populates='habits')
    checks = orm.relationship('HabitCheck', back_populates='habit', cascade='all, delete-orphan')


class HabitCheck(SqlAlchemyBase):
    __tablename__ = 'habit_checks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    habit_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("habits.id"))
    check_date = sqlalchemy.Column(sqlalchemy.Date, default=datetime.datetime.now)
    checked_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    habit = orm.relationship('Habit', back_populates='checks')