from client.client import OrionClient
from utils.hosts import LOCAL


if __name__ == '__main__':
    # Register to any notification in Orion.
    orion = OrionClient(host=LOCAL)

    entity_id = '.*'
    # notify_url = 'http://quantumleap:8668/notify'
    notify_url = 'http://192.0.0.1:8668/notify'
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
              {
                "idPattern": entity_id,
                "type": "thing"
              }
            ],
            "condition": {
              "attrs": [
                "temperature",
              ]
            }
          },
        "notification": {
            "http": {
              "url": notify_url
            },
            "attrs": [
                "temperature",
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }
    res = orion.subscribe(subscription)
    print(res.text)
