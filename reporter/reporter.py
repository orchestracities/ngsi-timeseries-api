"""
The reporter is the service responsible for handling NGSI notifications, validating them, and feeding the corresponding
updates to the translator.

The reporter needs to know the form of the entity (i.e, name and types of its attributes). There are two approaches:
    1 - Clients tell reporter which entities they care about and Reporter goes find the metadata in Context Broker
    2 - The reporter only consumes the Context Broker notifications and builds little by little the whole entity.
        In this case, the notifications must come with some mimimum amount of required data (e.g, entity_type,
        entity_id, a time index and the updated value[s]). Ideally, in the first notification the reporter would be
        notified of all the entity attributes so that it can tell the translator how to create the complete
        corresponding table[s] in the database.

For now, we have adopted approach 2.
"""
from flask import Flask, request
from utils.common import iter_entity_attrs
from utils.hosts import LOCAL
from datetime import datetime
import logging
import os
import warnings

app = Flask('reporter')


@app.route('/version')
def version():
    return '0.0.1'


def _validate_payload(payload):
    """
    :param payload:
        The received json data in the notification.
    :return: str | None
        Error message, if any.
    """
    # The entity must be uniquely identifiable
    if 'type' not in payload:
        return 'Entity type is required in notifications'

    # TODO: State that pattern-based ids or types are not yet supported.
    if 'id' not in payload:
        return 'Entity id is required in notifications'

    # There must be at least one attribute other than id and type (i.e, the changed value)
    attrs = list(iter_entity_attrs(payload))
    if len(attrs) == 0:
        return 'Received notification without attributes other than "type" and "id"'

    # Attributes must have a value and the modification time
    for attr in attrs:
        if 'value' not in payload[attr] or payload[attr]['value'] == '':
            return 'Payload is missing value for attribute {}'.format(attr)

        if 'dateModified' not in payload[attr]['metadata']:
            warnings.warn("Attribute '{}' did not include a dateModified. Assuming notification arrival time.".format(attr))


def _get_time_index(payload):
    """
    :param payload:
        The received json data in the notification.

    :return: str
        The notification time index. E.g: '2017-06-29T14:47:50.844'

    The strategy for now is simple. Received notifications are expected to have the dateModified field
    (http://docs.orioncontextbroker.apiary.io/#introduction/specification/virtual-attributes). If the notification lacks
    this attribute, the received time will be assumed.

    In future, this could be enhanced with customs notifications where user specifies which attribute is to be used as
    "time index".
    """
    if 'dateModified' in payload:
        return payload['dateModified']

    for attr in iter_entity_attrs(payload):
        if 'metadata' in payload[attr] and 'dateModified' in payload[attr]['metadata']:
            return payload[attr]['metadata']['dateModified']['value']

    # Assume current timestamp as dateModified
    return datetime.now().isoformat()


@app.route('/notify', methods=['POST', 'GET'])
def notify():
    payload = request.json['data']
    assert len(payload) == 1, 'Multiple data elements in notifications not supported yet'
    payload = payload[0]

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Received payload: {}'.format(payload))

    # Validate notification
    error = _validate_payload(payload)
    if error:
        return error, 400

    # Add TIME_INDEX attribute
    from translators.crate import CrateTranslator
    payload[CrateTranslator.TIME_INDEX_NAME] = _get_time_index(payload)

    # Send valid entity to translator
    DB_HOST = os.environ.get('CRATE_HOST', 'crate')
    DB_PORT = 4200
    DB_NAME = "ngsi-tsdb"
    with CrateTranslator(DB_HOST, DB_PORT, DB_NAME) as trans:
        trans.insert([payload])

    msg = "Notification successfully processed"
    logger.info(msg)
    return msg


if __name__ == '__main__':
    app.run(host=LOCAL, port=8668)

# TODO: Consider offering an API endpoint to receive just the user's entities of interest and make QL actually perform
# the corresponding subscription to orion. I.e, QL must be told where orion is.
