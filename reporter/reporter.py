"""
The reporter is the service responsible for handling NGSI notifications and feeding the corresponding updates to the
translator.

The reporter needs to know the form of the entity (i.e, name and types of its attributes). There are two approaches:
    - Clients tell reporter which entities they care about and Reporter goes find the metadata in Context Broker
    - The reporter only consumes the Context Broker notifications and builds little by little the whole entity.
        In this case, the notifications must come with some mimimum amount of required data (e.g, entity_type,
        entity_id, a time index and the updated value[s]). Ideally, in the first notification the reporter would be
        notified of all the entity attributes so that it can tell the translator how to create the complete
        corresponding table[s] in the database.
"""
from flask import Flask, request, g
from translators.crate import CrateTranslator
from utils.hosts import LOCAL

app = Flask('reporter')

PORT = 8668

DB_HOST = LOCAL
DB_PORT = 4200
DB_NAME = "ngsi-tsdb"


@app.route('/version')
def version():
    return '0.0.1'


def _validate_payload(payload):
    # Validate notification
    if 'type' not in payload:
        return 'Entity type is required in notifications'

    if 'id' not in payload:
        return 'Entity id is required in notifications'

    # TODO: State that pattern-based ids or types are not yet supported.

    attrs = payload.keys() - set(['type', 'id'])
    for at in attrs:
        if 'dateModified' not in payload[at]['metadata']:
            return 'Modified attributes must come with dateModified metadata. ' \
                   'Include "metadata": [ "dateModified" ] in your notification params.'

    # there must be at least one attribute other than id and type (i.e, the changed value)
    if len(attrs) == 0:
        return 'Received notification without attributes other than "type" and "id"'


@app.route('/notify', methods=['POST', 'GET'])
def notify():
    # Let's inspect what we have in the notification.
    payload = request.json['data']
    assert len(payload) == 1, 'Multiple data elements in notifications not supported yet'
    payload = payload[0]

    error = _validate_payload(payload)
    if error:
        return error, 400

    # Send valid entity to translator
    # with CrateTranslator(DB_HOST, DB_PORT, DB_NAME) as trans:
    #     res = trans.insert(payload)

    return "Notification successfully processed"


if __name__ == '__main__':
    app.run(host=LOCAL, port=PORT)
