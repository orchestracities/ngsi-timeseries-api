from utils.subscription_dsl import *


def build_subscription(quantumleap_url,
                       etype, eid, eid_pattern,
                       observed_attributes, notified_attributes,
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
                attrs(observed_attributes)
            )
        ),
        notification(
            url('{}/notify'.format(quantumleap_url)),
            metadata(['dateCreated', 'dateModified']),
            attrs(notified_attributes)
        ),
        throttling(throttling_secs)
    )

    return tree.to_dict()
