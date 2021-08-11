TIME_INDEX_NAME = 'time_index'


def entity_pk(entity):
    """
    :param entity: NGSI JSON Entity Representation
    :return: unicode NGSI Entity "unique" identifier.
    """
    if 'type' not in entity and 'id' not in entity:
        # Allowance for tsdb back-and-forth.
        # To avoid column name id in databases, we prefix it with entity_. Same
        # for type, for consistence.
        t, i = entity['entity_type'], entity['entity_id']
    else:
        t, i = entity['type'], entity['id']
    return "t:{}i:{}".format(t, i)


def iter_entity_attrs(entity):
    for attr in entity:
        if attr not in ['type', 'id', '@context']:
            yield attr
