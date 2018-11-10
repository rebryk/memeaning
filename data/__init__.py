import json

from pony import orm

db = orm.Database()

from .meme import Meme
from .image import Image
from .question import Question

with open('config/db.json') as f:
    config = json.load(f)
    db.bind(provider='postgres',
            user=config['user'],
            password=config['password'],
            host=config['host'],
            database=config['database'])

    db.generate_mapping(create_tables=True)

__all__ = ['Meme', 'Image', 'Question']
