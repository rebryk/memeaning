import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pony.orm import db_session

from data import Meme

_HOST = 'https://knowyourmeme.com'

logger = logging.getLogger(__name__)


def _extract_meme_urls(page: BeautifulSoup) -> [str]:
    urls = set()

    for href in map(lambda tag: tag.get('href'), page.find_all(name='a', attrs={'class': 'photo'})):
        if href and str.startswith(href, '/static/'):
            urls.add(urlparse(href).path)

    return urls


@db_session
def _parse_meme_page(page_url: str):
    response = requests.get(page_url, headers={'user-agent': 'vkhack-bot'})
    parsed_page = BeautifulSoup(response.text, "html.parser")

    image = parsed_page.find(name='a', attrs={'class': 'photo left wide'})

    if image is None:
        image = parsed_page.find(name='a', attrs={'class': 'photo left '})

    image = image.get('href')
    about_tag = parsed_page.find(name='h2', attrs={'id': 'about'})
    after_about_tag = list(about_tag.next_siblings)[1]

    origin = None
    origin_tag = parsed_page.find(name='h2', attrs={'id': 'origin'})

    if origin_tag:
        after_origin_tag = list(origin_tag.next_siblings)[1]
        origin = after_origin_tag.text

    name = list(after_about_tag.children)[0].text
    about = after_about_tag.text

    if not all(ch.isalpha() or ch in ' .,?!-\"\'' for ch in name):
        return

    type_tags = parsed_page.find_all(name='a', attrs={'class': 'entry-type-link'})
    meme_type = ','.join(tag.text for tag in type_tags)

    if not Meme.exists(name=name):
        logger.info(f'Add meme {page_url}')
        Meme(name=name, image=image, about=about, origin=origin, type=meme_type)


def _parse_page(page_url: str):
    response = requests.get(page_url, headers={'user-agent': 'vkhack-bot'})
    parsed_page = BeautifulSoup(response.text, "html.parser")

    for meme_url in _extract_meme_urls(parsed_page):
        try:
            _parse_meme_page(_HOST + meme_url)
        except Exception:
            logger.error(f'Failed to parse {meme_url}')


def parse_know_your_meme(page_from: int, page_to: int):
    for page_id in range(page_from, page_to):
        logger.info(f'Parse page {page_id}')
        _parse_page(_HOST + '/static/popular/page/' + str(page_id))
