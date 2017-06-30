from translators.crate import CrateTranslator
from utils.common import create_random_entities
from utils.hosts import LOCAL
import time


def feed():
    client = CrateTranslator(LOCAL)
    client.setup()

    try:
        while 1:
            entities = create_random_entities(1, 2, 1, use_time=True, use_geo=True)
            client.insert(entities)
            time.sleep(60)
    finally:
        client.dispose()


if __name__ == '__main__':
    feed()
