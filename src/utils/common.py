import logging
import default


def log():
    logger = logging.getLogger(__name__)
    return logger

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


def has_value(entity, attr_name):
    attr = entity.get(attr_name, {})
    attr_value = None
    if attr is None:
        attr = {}
    elif isinstance(attr, dict):
        attr_value = attr.get('value', None)
        attr_type = attr.get('type', None)
        if attr_value is None:
            return False
        # work around to not drop during validation `modifiedAt` and `observedAt`
        if is_text(attr_type):
            return True
    else:
        attr_value = attr

    if isinstance(attr_value, str):
        attr_value = attr_value.strip()

    # If type != Text and value == '', make value = null
    return attr_value != '' and attr_value is not None


def is_text(attr_type):
    return attr_type == default.NGSI_TEXT


def validate_entity(cls, values):
    """
    :param attributes:
        The received json data in the notification.
    :return: attributes
        Validated attributes.
    """
    # The entity must be uniquely identifiable
    assert 'type' in values, 'Entity type is required in notifications'
    assert 'id' in values, 'Entity id is required in notifications'

    # There should be at least one attribute other than id and type
    # (i.e, the changed value)
    attrs = list(iter_entity_attrs(values))
    assert len(attrs) != 0, 'Entity has only id and type'

     # Attributes should have a value and the modification time
    for attr in attrs:
        if not has_value(values, attr):
            values[attr].update({'value': None})
            log().warning(
                'An entity update is missing value '
                'for attribute {}'.format(attr))
    return values
