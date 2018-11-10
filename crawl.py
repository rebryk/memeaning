import argparse
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

from crawlers import parse_know_your_meme
from crawlers import parse_imgflip
from pony import orm
from data import Meme

parser = argparse.ArgumentParser('Parse static.')
parser.add_argument('--resource', type=str, required=True, help='resource to parse')
parser.add_argument('--page_from', type=int, required=True, help='start page')
parser.add_argument('--page_to', type=int, required=True, help='end page')

if __name__ == '__main__':
    args = parser.parse_args()

    if args.resource == 'know_your_meme':
        parse_know_your_meme(args.page_from, args.page_to)
    elif args.resource == 'imgflip':
        with orm.db_session():
            for meme in Meme.select():
                parse_imgflip(meme.id, meme.name)
    else:
        raise RuntimeError(f'No such resource: {args.resource}')
