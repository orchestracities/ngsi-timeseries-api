import connexion
import six

from swagger_server.models.entity import Entity  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server import util


def get_attribute_data(entityId, attrName, type=None):  # noqa: E501
    """get_attribute_data

    Returns a JSON object with the attribute data of the attribute. The object follows the JSON Representation for attributes (described in \&quot;JSON Attribute Representation\&quot; section). Response: * Successful operation uses 200 OK. * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity
    :type entityId: str
    :param attrName: Name of the attribute to be retrieved.
    :type attrName: str
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str

    :rtype: Entity
    """
    return 'do some magic!'


def remove_a_single_attribute(entityId, attrName, type=None):  # noqa: E501
    """remove_a_single_attribute

    Removes an entity attribute. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity.
    :type entityId: str
    :param attrName: Attribute name.
    :type attrName: str
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str

    :rtype: None
    """
    return 'do some magic!'


def update_attribute_data(entityId, attrName, body, type=None):  # noqa: E501
    """update_attribute_data

    The request payload is an object representing the new attribute data. Previous attribute data is replaced by the one in the request. The object follows the JSON Representation for attributes (described in \&quot;JSON Attribute Representation\&quot; section). Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity to update
    :type entityId: str
    :param attrName: Attribute name
    :type attrName: str
    :param body: 
    :type body: 
    :param type: Entity type, to avoid ambiguity in case there are several entities with the same entity id.
    :type type: str

    :rtype: None
    """
    return 'do some magic!'
