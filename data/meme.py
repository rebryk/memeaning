from pony import orm

from . import db


class Meme(db.Entity):
    name = orm.Required(str)
    imgflip = orm.Optional(str)
    year = orm.Optional(str)
    type = orm.Optional(str)
    likes = orm.Required(int, default=0)
    image = orm.Required(str)
    about = orm.Required(str)
    origin = orm.Optional(str)
