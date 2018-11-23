from utils.subscription_dsl import *


def build_subscription(quantumleap_url,
                       etype, eid, eid_pattern,
                       attributes, observed_attributes, notified_attributes,
                       throttling_secs):
    tree = subscription(
        description('Created by QuantumLeap {}.'.format(quantumleap_url)),
        subject(
            entities(
                entity(
                    entity_type(etype),
                    entity_id(eid, eid_pattern)
                )
            ),
            condition(
                attrs(first_of(attributes, observed_attributes))
            )
        ),
        notification(
            url('{}/notify'.format(quantumleap_url)),
            metadata(['dateCreated', 'dateModified']),
            attrs(first_of(attributes, notified_attributes))
        ),
        throttling(throttling_secs)
    )

    return tree.to_dict()
