from utils.subscription_dsl import *
from .timex import TIME_INDEX_HEADER_NAME


def build_subscription(quantumleap_url,
                       etype, eid, eid_pattern,
                       attributes, observed_attributes, notified_attributes,
                       throttling_secs,
                       time_index_attribute=None):
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
            build_notification_target(quantumleap_url, time_index_attribute),
            metadata(['dateCreated', 'dateModified', 'TimeInstant']),
            attrs(first_of(attributes, notified_attributes))
        ),
        throttling(throttling_secs)
    )

    return tree.to_dict()


def build_notification_target(quantumleap_url, time_index_attribute):
    notification_endpoint = '{}/notify'.format(quantumleap_url)
    if time_index_attribute:
        return custom(
                   notification_endpoint,
                   headers(
                       time_index_header(time_index_attribute)
                   )
                )
    return url(notification_endpoint)


def time_index_header(time_index_attribute):
    return http_header(TIME_INDEX_HEADER_NAME, time_index_attribute)
