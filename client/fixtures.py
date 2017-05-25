import pymongo as pm
import pytest
from client.client import OrionClient
from utils.hosts import LOCAL


MONGO_HOST = ORION_HOST = LOCAL
MONGO_PORT = 27017
ORION_PORT = 1026


@pytest.fixture
def fresh_db():
    db_client = pm.MongoClient(MONGO_HOST, 27017)
    db_client.drop_database("orion")
    db_client.drop_database("orion-default")


@pytest.fixture
def orion_client():
    client = OrionClient(ORION_HOST, ORION_PORT)
    yield client
