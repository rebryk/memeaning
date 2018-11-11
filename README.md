
# MeMeaning
Backend for MeMeaning project.

## Installation
Please, clone this repository and install python requirements:
```
git clone https://github.com/rebryk/memeaning.git
cd memeaning
pip3 install -r requirements.txt
```
Except this you should clone [this](https://github.com/stasbel/Meme-Machinery-VKHack2018) repository to provide meme generation:
```
git clone https://github.com/stasbel/Meme-Machinery-VKHack2018.git
cd Meme-Machinery-VKHack2018
python setup.py develop
```
## Database
First of all you need to setup [PostgreSQL](https://www.postgresql.org) server to store all data. <br>
Please, create `db.json` in `config` folder with the following information:
```
{
  "database": <database name>,
  "user": <postgres user>,
  "password": <password>,
  "host": "localhost"
}
```

## Crawle data
You should crawl [Know Your Meme](http://knowyourmeme.com/) to get more mems, right? <br>
Run `python crawl.py --resource know_your_meme --pages_from 1 --pages_to 40`

Awesome! Right know you have some memes! But you do not have other people's memes!
Run `python crawl.py --resource imgflip` to download them from [imgflip](https://imgflip.com).

## Usage
Finally you can spin server with the following command:
```
python server.py -i
```
