"""
Simple script to feed CrateDB with random entities every SLEEP seconds.
"""
from conftest import do_clean_crate
from translators.crate import CrateTranslator
from utils.common import create_random_entities
from utils.hosts import LOCAL
import time

SLEEP = 6


def feed():
    client = CrateTranslator(LOCAL)
    client.setup()

    try:
        while 1:
            entities = create_random_entities(1, 1, 1, use_time=True, use_geo=True)
            client.insert(entities)
            print('Inserted: {}'.format(entities[0]))
            time.sleep(SLEEP)
    finally:
        client.dispose()
        do_clean_crate()


if __name__ == '__main__':
    feed()
