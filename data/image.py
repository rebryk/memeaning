from pony import orm

from . import db


class Image(db.Entity):
    meme = orm.Required(int)
    url = orm.Required(str)
