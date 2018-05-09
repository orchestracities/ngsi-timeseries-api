from client.client import OrionClient
import os
import pymongo as pm
import pytest

MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
ORION_HOST = os.environ.get('ORION_HOST', 'orion')
ORION_PORT = os.environ.get('ORION_PORT', 1026)


def do_clean_mongo():
    db_client = pm.MongoClient(MONGO_HOST, MONGO_PORT)
    for db in db_client.database_names():
        db_client.drop_database(db)


@pytest.fixture
def clean_mongo():
    yield
    do_clean_mongo()


@pytest.fixture
def orion_client():
    client = OrionClient(ORION_HOST, ORION_PORT)
    yield client


