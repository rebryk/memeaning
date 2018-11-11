import io
import logging
import pickle
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import face_recognition
import numpy as np
import requests
import torch
from PIL import Image as PILImage
from flask import Flask, jsonify, request
from flask_cors import CORS
from memgen.sampler import TextSampler
from memgen.stages.printer import Printer
from memsearch.text import TextSearcher
from pony import orm

from data import Image
from data import Meme
from data import Question
from search import ISearcher


class Server:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MATRIX_PATH = Path('gen_data/matrix.npy')
    NEW_META_PATH = Path('gen_data/processed_reddit_data.pth')
    IMAGE_FOLDER = Path('images')
    PAINTING_FOLDER = 'painting'

    matrix = np.load(MATRIX_PATH)
    meta = torch.load(NEW_META_PATH)
    sampler = TextSampler(matrix, meta)
    printer = Printer()

    with open(f'latent_space/{PAINTING_FOLDER}.p', 'rb') as fp:
        paintings = pickle.load(fp)

    app = Flask(__name__, static_folder='static')
    CORS(app)

    isearcher = ISearcher(IMAGE_FOLDER)
    tsearcher = TextSearcher()

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, host: str):
        self.app.run(host=host)

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Server.ALLOWED_EXTENSIONS

    @orm.db_session
    def download_images(self):
        self.logger.info('Downloading images...')

        if not self.IMAGE_FOLDER.exists():
            self.IMAGE_FOLDER.mkdir()

        for meme in Meme.select():
            image = self.IMAGE_FOLDER / str(meme.id)

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
    @app.route('/isearch', methods=['POST'])
    @orm.db_session
    def image_search():
        file = request.files['file']
        if file and Server.allowed_file(file.filename):
            image = PILImage.open(io.BytesIO(file.read()))
            result = Server.isearcher.search_img(image, top_k=3)
            return jsonify({'results': result})

    @staticmethod
    @app.route('/search')
    @orm.db_session
    def text_search():
        query = request.args.get('q')
        result = list(map(str, Server.tsearcher.search(query)[:3]))
        return jsonify({'results': result})

    @staticmethod
    @app.route('/generate', methods=['POST'])
    def generate_meme():
        id_ = int(request.values['id'])
        file = request.files['file']
        if file and Server.allowed_file(file.filename):
            image = PILImage.open(io.BytesIO(file.read()))

            if id_ == 1:
                text = Server.sampler.sample(image)
                meme = Server.printer.print(image, text)
            else:
                image = np.array(image.convert('RGB'))
                embeddings = face_recognition.face_encodings(image)

                if len(embeddings) > 0:
                    photo = embeddings[0]
                    key = min(Server.paintings.items(), key=lambda x: np.sum(np.sqrt((photo - np.array(x[1])) ** 2)))[0]
                else:
                    key = random.choice(list(Server.paintings.keys()))

                folder = '' if key[0] == '1' else ' 2'
                file_to_load = f'dataset_updated/{folder}/training_set/{Server.PAINTING_FOLDER}/{key[1:]}.jpg'
                meme = PILImage.open(file_to_load)

            current_date = datetime.now().strftime('%Y.%m.%d %H.%M.%S')
            file_name = f'{current_date}.png'
            meme.save(f'static/{file_name}')
            return jsonify({'result': quote_plus(file_name)})

    @staticmethod
    @app.route('/quiz')
    @orm.db_session
    def get_quiz():
        id = int(request.args.get('id'))
        return jsonify({'id': id,
                        'questions': [{'text': q.text,
                                       'answer': q.answer,
                                       'static': [q.meme_1, q.meme_2, q.meme_3]}
                                      for q in Question.select(lambda it: it.quiz == id)]})

    @orm.db_session
    def build_text_index(self):
        data = [(it.id, it.about) for it in Meme.select()]
        self.tsearcher.build_index(data)

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
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    server = Server()

    # Build text index
    # server.build_text_index()

    server.download_images()
    server.run('0.0.0.0')
