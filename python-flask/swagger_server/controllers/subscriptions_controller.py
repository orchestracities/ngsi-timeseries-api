import connexion
import six

from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.models.subscription import Subscription  # noqa: E501
from swagger_server import util


def create_a_new_subscription(body):  # noqa: E501
    """create_a_new_subscription

    Creates a new subscription. The subscription is represented by a JSON object as described at the beginning of this section. Response: * Successful operation uses 201 Created * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Subscription.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_subscription(subscriptionId):  # noqa: E501
    """delete_subscription

    Cancels subscription. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param subscriptionId: subscription Id.
    :type subscriptionId: str

    :rtype: None
    """
    return 'do some magic!'


def retrieve_subscription(subscriptionId):  # noqa: E501
    """retrieve_subscription

    The response is the subscription represented by a JSON object as described at the beginning of this section. Response: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param subscriptionId: subscription Id.
    :type subscriptionId: str

    :rtype: Subscription
    """
    return 'do some magic!'


def retrieve_subscriptions(limit=None, offset=None, options=None):  # noqa: E501
    """retrieve_subscriptions

    Returns a list of all the subscriptions present in the system. Response: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param limit: Limit the number of types to be retrieved
    :type limit: float
    :param offset: Skip a number of records
    :type offset: float
    :param options: Options dictionary
    :type options: str

    :rtype: List[Subscription]
    """
    return 'do some magic!'


def update_subscription(subscriptionId, body):  # noqa: E501
    """update_subscription

    Only the fields included in the request are updated in the subscription. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param subscriptionId: subscription Id.
    :type subscriptionId: str
    :param body: 
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Subscription.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
