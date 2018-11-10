import logging

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
from flask import Flask, jsonify, request
from flask_cors import CORS
from pony import orm
from data import Meme
from data import Image
from data import Question
from pathlib import Path
from search import ISearcher


class Server:
    app = Flask(__name__)
    CORS(app)

    isearcher = ISearcher('images')

    def __init__(self, path: str):
        self.path = path
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, host: str):
        self.app.run(host=host)

    @orm.db_session
    def download_images(self):
        self.logger.info('Downloading images...')
        folder = Path(self.path)

        if not folder.exists():
            folder.mkdir()

        for meme in Meme.select():
            image = folder / str(meme.id)

            if not image.exists():
                r = requests.get(meme.image, stream=True)

                if r.status_code == 200:
                    with image.open('wb') as f:
                        for chunk in r:
                            f.write(chunk)

    @staticmethod
    @app.route('/memes')
    @orm.db_session
    def get_memes():
        id = request.args.get('id')

        if id is not None and Meme.exists(id=int(id)):
            return jsonify(Server._get_meme_long_desc(Meme.get(id=int(id))))

        memes = [Server._get_meme_short_desc(meme) for meme in Meme.select()]

        memes.append(Server._get_quiz_desc(1))
        memes.append(Server._get_generator_desc(1))
        memes.append(Server._get_generator_desc(2))

        return jsonify(memes)

    @staticmethod
    @app.route('/quiz')
    @orm.db_session
    def get_quiz():
        id = int(request.args.get('id'))
        return jsonify({'id': id,
                        'questions': [{'text': q.text,
                                       'answer': q.answer,
                                       'memes': [q.meme_1, q.meme_2, q.meme_3]}
                                      for q in Question.select(lambda it: it.quiz == id)]})

    @staticmethod
    @orm.db_session
    def _get_meme_long_desc(meme) -> dict:
        return {'id': meme.id,
                'url': meme.image,
                'name': meme.name,
                'about': meme.about,
                'origin': meme.origin,
                'tags': meme.type.split(',') if meme.type else [],
                'images': list(map(lambda it: it.url, Image.select(lambda it: it.meme == meme.id)))}

    @staticmethod
    @orm.db_session
    def _get_meme_short_desc(meme) -> dict:
        return {'id': meme.id,
                'quiz': None,
                'generator': None,
                'url': meme.image,
                'about': meme.about}

    @staticmethod
    @orm.db_session
    def _get_quiz_desc(quiz_id: int) -> dict:
        return {'quiz': quiz_id}

    @staticmethod
    @orm.db_session
    def _get_generator_desc(generator_id: int) -> dict:
        return {'generator': generator_id}


if __name__ == "__main__":
    server = Server('images')
    server.download_images()
    server.run('0.0.0.0')
