from os import environ

REDDIT_CLIENT_ID = environ['REDDIT_CLIENT_ID'] if 'REDDIT_CLIENT_ID' in environ else ''
REDDIT_CLIENT_SECRET = environ['REDDIT_CLIENT_SECRET'] if 'REDDIT_CLIENT_SECRET' in environ else ''
REDDIT_USERNAME = environ['REDDIT_USERNAME'] if 'REDDIT_USERNAME' in environ else ''
REDDIT_PASSWORD = environ['REDDIT_PASSWORD'] if 'REDDIT_PASSWORD' in environ else ''
DB_USER = environ['DB_USER'] if 'DB_USER' in environ else ''
DB_PASSWORD = environ['DB_PASSWORD'] if 'DB_PASSWORD' in environ else ''
DB_HOST = environ['DB_HOST'] if 'DB_HOST' in environ else ''
DB_DATABASE = environ['DB_DATABASE'] if 'DB_DATABASE' in environ else ''
