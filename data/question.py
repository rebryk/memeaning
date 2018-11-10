from pony import orm

from . import db


class Question(db.Entity):
    quiz = orm.Required(int)
    text = orm.Required(str)
    answer = orm.Required(int)
    meme_1 = orm.Required(int)
    meme_2 = orm.Required(int)
    meme_3 = orm.Required(int)
