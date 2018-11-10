import logging
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pony.orm import db_session

from data import Image

_HOST = 'https://imgflip.com'

logger = logging.getLogger(__name__)


def _extract_meme_urls(page: BeautifulSoup) -> [str]:
    urls = set()

    for href in map(lambda tag: tag.get('src'), page.find_all(name='img', attrs={'class': 'base-img'})):
        urls.add(href)

    return urls


@db_session
def _parse_page(meme_id: int, page_url: str):
    response = requests.get(page_url, headers={'user-agent': 'vkhack-bot'})
    parsed_page = BeautifulSoup(response.text, "html.parser")

    for meme_url in _extract_meme_urls(parsed_page):
        url = f'https:' + meme_url

        if not Image.exists(url=url):
            logger.info(f'Add image {url}')
            Image(meme=meme_id, url=url)


def parse_imgflip(meme_id: int, name: str):
    page_url = f'https://imgflip.com/search?q={quote_plus(name)}'

    response = requests.get(page_url, headers={'user-agent': 'vkhack-bot'})
    parsed_page = BeautifulSoup(response.text, "html.parser")
    meme_title = parsed_page.find(name='h2', attrs={'class': 's-results-title'})

    if meme_title is None:
        return

    if meme_title.text != 'Memes':
        return

    urls = set()

    for tag in meme_title.next_siblings:
        if not isinstance(tag, Tag):
            continue

        if tag.name != 'a':
            break

        href = tag.get('href')

        if 's-result' not in tag.attrs.get('class') or not href:
            continue

        urls.add(_HOST + href)

    for url in urls:
        logger.info(f'Parse page {url}')
        _parse_page(meme_id, url)
