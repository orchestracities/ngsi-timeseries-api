import connexion
import six

from swagger_server.models.api_entry_point import APIEntryPoint  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server import util


def retrieve_api_resources():  # noqa: E501
    """retrieve_api_resources

    This resource does not have any attributes. Instead it offers the initial API affordances in the form of the links in the JSON body. It is recommended to follow the “url” link values, [Link](https://tools.ietf.org/html/rfc5988) or Location headers where applicable to retrieve resources. Instead of constructing your own URLs, to keep your client decoupled from implementation details. # noqa: E501


    :rtype: APIEntryPoint
    """
    return 'do some magic!'
