import connexion
import six

from swagger_server.models.entity_type import EntityType  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server import util


def retrieve_entity_type(entityType):  # noqa: E501
    """retrieve_entity_type

    This operation returns a JSON object with information about the type: * &#x60;attrs&#x60; : the set of attribute names along with all the entities of such type, represented in   a JSON object whose keys are the attribute names and whose values contain information of such   attributes (in particular a list of the types used by attributes with that name along with all the   entities). * &#x60;count&#x60; : the number of entities belonging to that type.  Response code: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityType: Entity Type
    :type entityType: str

    :rtype: EntityType
    """
    return 'do some magic!'


def retrieve_entity_types(limit=None, offset=None, options=None):  # noqa: E501
    """retrieve_entity_types

    If the &#x60;values&#x60; option is not in use, this operation returns a JSON array with the entity types. Each element is a JSON object with information about the type: * &#x60;type&#x60; : the entity type name. * &#x60;attrs&#x60; : the set of attribute names along with all the entities of such type, represented in   a JSON object whose keys are the attribute names and whose values contain information of such   attributes (in particular a list of the types used by attributes with that name along with all the   entities). * &#x60;count&#x60; : the number of entities belonging to that type. If the &#x60;values&#x60; option is used, the operation returns a JSON array with a list of entity type names as strings. Results are ordered by entity &#x60;type&#x60; in alphabetical order.  Response code: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param limit: Limit the number of types to be retrieved.
    :type limit: float
    :param offset: Skip a number of records.
    :type offset: float
    :param options: Options dictionary.
    :type options: str

    :rtype: List[EntityType]
    """
    return 'do some magic!'
