import json
import logging
import os
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from memgen.stages.embedder import Embedder
from memgen.stages.matcher import Matcher


class ISearcher:
    DUMP_FOLDER = Path('embeddings')
    EMBEDDING_DUMP = DUMP_FOLDER / 'embeddings.npy'
    MAPPING_DUMP = DUMP_FOLDER / 'mapping.txt'
    EMBEDDING_SIZE = 2048

    def __init__(self, path: str):
        self.path = path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.embedder = Embedder()
        embeddings, mapping = self._build_index()
        self.index_to_id = mapping
        self.matcher = Matcher(embeddings)

    def search_img(self, img, top_k: int = 1):
        results = [self.index_to_id[str(idx)] for idx in self.matcher.match(img, top_k)]
        self.logger.info(f'Search results: {results}')
        return results

    def search(self, url: str, top_k: int = 1):
        self.logger.info(f'Searching for {url}')
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return self.search_img(img, top_k)

    def _load_images(self):
        for file_name in os.listdir(self.path):
            image_id = file_name
            image_data = Image.open(os.path.join(self.path, file_name))
            yield (image_id, image_data)

    def _build_index(self):
        if not self.DUMP_FOLDER.exists():
            self.DUMP_FOLDER.mkdir()

        if self.EMBEDDING_DUMP.exists():
            embeddings = np.load(str(self.EMBEDDING_DUMP))

            with self.MAPPING_DUMP.open('r') as f:
                mapping = json.load(f)
        else:
            images = list(self._load_images())
            embeddings = np.zeros((len(images), self.EMBEDDING_SIZE))
            mapping = {}

            for index, (image_id, img) in enumerate(images):
                mapping[index] = image_id
                embeddings[index] = self.embedder.embed(img)

            np.save(str(self.EMBEDDING_DUMP), embeddings)
            with self.MAPPING_DUMP.open('w') as f:
                json.dump(mapping, f)

        return embeddings, mapping
