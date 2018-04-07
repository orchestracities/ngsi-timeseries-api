import connexion
import six

from swagger_server.models.batch_operation import BatchOperation  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.models.query import Query  # noqa: E501
from swagger_server import util


def query(body, limit=None, offset=None, orderBy=None, options=None):  # noqa: E501
    """query

    The response payload is an Array containing one object per matching entity, or an empty array &#x60;[]&#x60; if  no entities are found. The entities follow the JSON entity Representation format (described in the section \&quot;JSON Entity Representation\&quot;). The payload may contain the following elements (all of them optional): + &#x60;entities&#x60;: a list of entites to search for. Each element is represented by a JSON object with the   following elements:     + &#x60;id&#x60; or &#x60;idPattern&#x60;: Id or pattern of the affected entities. Both cannot be used at the same       time, but at least one of them must be present.     + &#x60;type&#x60; or &#x60;typePattern&#x60;: Type or type pattern of the entities to search for. Both cannot be used at       the same time. If omitted, it means \&quot;any entity type\&quot;. + &#x60;attributes&#x60;: a list of attribute names to search for. If omitted, it means \&quot;all attributes\&quot;.  Response code: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param body: 
    :type body: dict | bytes
    :param limit: Limit the number of entities to be retrieved.
    :type limit: float
    :param offset: Skip a number of records.
    :type offset: float
    :param orderBy: Criteria for ordering results. See \&quot;Ordering Results\&quot; section for details.
    :type orderBy: str
    :param options: Options dictionary
    :type options: str

    :rtype: List[object]
    """
    if connexion.request.is_json:
        body = Query.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update(body, options=None):  # noqa: E501
    """update

    This operation allows to create, update and/or delete several entities in a single batch operation. The payload is an object with two properties: + &#x60;actionType&#x60;, to specify the kind of update action to do: either APPEND, APPEND_STRICT, UPDATE,   DELETE. + &#x60;entities&#x60;, an array of entities, each one specified using the JSON entity Representation format   (described in the section \&quot;JSON Entity Representation\&quot;). Response: * Successful operation uses 204 No Content. * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param body: 
    :type body: dict | bytes
    :param options: Options dictionary
    :type options: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = BatchOperation.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
