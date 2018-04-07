import connexion
import six

from swagger_server.models.attribute import Attribute  # noqa: E501
from swagger_server.models.entity import Entity  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server import util


def create_entity(body, options=None):  # noqa: E501
    """create_entity

    The payload is an object representing the entity to be created. The object follows the JSON entity Representation format (described in a \&quot;JSON Entity Representation\&quot; section). Response: * Successful operation uses 201 Created. Reponse includes a &#x60;Location&#x60; header with the URL of the   created entity. * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param body: JSON Entity Representation
    :type body: dict | bytes
    :param options: Options dictionary
    :type options: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = Entity.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def list_entities(id=None, type=None, idPattern=None, typePattern=None, q=None, mq=None, georel=None, geometry=None, coords=None, limit=None, offset=None, attrs=None, orderBy=None, options=None):  # noqa: E501
    """list_entities

    Retrieves a list of entities that match different criteria by id, type, pattern matching (either id or type) and/or those which match a query or geographical query (see [Simple Query Language](#simple_query_language) and  [Geographical Queries](#geographical_queries)). A given entity has to match all the criteria to be retrieved (i.e., the criteria is combined in a logical AND way). Note that pattern matching query parameters are incompatible (i.e. mutually exclusive) with their corresponding exact matching parameters, i.e. &#x60;idPattern&#x60; with &#x60;id&#x60; and &#x60;typePattern&#x60; with &#x60;type&#x60;. The response payload is an array containing one object per matching entity. Each entity follows the JSON entity Representation format (described in \&quot;JSON Entity Representation\&quot; section).  Response code: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param id: A comma-separated list of elements. Retrieve entities whose ID matches one of the elements in the list. Incompatible with idPattern.
    :type id: str
    :param type: comma-separated list of elements. Retrieve entities whose type matches one of the elements in the list. Incompatible with &#x60;typePattern&#x60;.
    :type type: str
    :param idPattern: A correctly formated regular expression. Retrieve entities whose ID matches the regular expression. Incompatible with id.
    :type idPattern: str
    :param typePattern: A correctly formated regular expression. Retrieve entities whose type matches the regular expression. Incompatible with &#x60;type&#x60;.
    :type typePattern: str
    :param q: A query expression, composed of a list of statements separated by &#x60;;&#x60;, i.e., q&#x3D;statement;statements;statement. See [Simple Query Language specification](#simple_query_language).
    :type q: str
    :param mq: A query expression for attribute metadata, composed of a list of statements separated by &#x60;;&#x60;, i.e., mq&#x3D;statement1;statement2;statement3. See [Simple Query Language specification](#simple_query_language).
    :type mq: str
    :param georel: Spatial relationship between matching entities and a reference shape. See [Geographical Queries](#geographical_queries).
    :type georel: str
    :param geometry: Geografical area to which the query is restricted. See [Geographical Queries](#geographical_queries).
    :type geometry: str
    :param coords: List of latitude-longitude pairs of coordinates separated by &#39;;&#39;. See [Geographical Queries](#geographical_queries).
    :type coords: str
    :param limit: Limits the number of entities to be retrieved
    :type limit: float
    :param offset: Establishes the offset from where entities are retrieved
    :type offset: float
    :param attrs: Comma-separated list of attribute names whose data are to be included in the response. The attributes are retrieved in the order specified by this parameter. If this parameter is not included, the attributes are retrieved in arbitrary order.
    :type attrs: str
    :param orderBy: Criteria for ordering results. See \&quot;Ordering Results\&quot; section for details.
    :type orderBy: str
    :param options: Options dictionary
    :type options: str

    :rtype: List[Entity]
    """
    return 'do some magic!'


def remove_entity(entityId, type=None):  # noqa: E501
    """remove_entity

    Delete the entity. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity to be deleted
    :type entityId: str
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str

    :rtype: None
    """
    return 'do some magic!'


def replace_all_entity_attributes(entityId, body, type=None, options=None):  # noqa: E501
    """replace_all_entity_attributes

    The request payload is an object representing the new entity attributes. The object follows the JSON entity Representation format (described in a \&quot;JSON Entity Representation\&quot; above), except that &#x60;id&#x60; and &#x60;type&#x60; are not allowed. The attributes previously existing in the entity are removed and replaced by the ones in the request. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity in question.
    :type entityId: str
    :param body: JSON Attribute Representation
    :type body: dict | bytes
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str
    :param options: Operations options
    :type options: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = Attribute.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def retrieve_entity(entityId, type=None, attrs=None, options=None):  # noqa: E501
    """retrieve_entity

    The response is an object representing the entity identified by the ID. The object follows the JSON entity Representation format (described in \&quot;JSON Entity Representation\&quot; section). This operation must return one entity element only, but there may be more than one entity with the same ID (e.g. entities with same ID but different types). In such case, an error message is returned, with the HTTP status code set to 409 Conflict. Response: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for more details. # noqa: E501

    :param entityId: Id of the entity to be retrieved
    :type entityId: str
    :param type: Entity type, to avoid ambiguity in case there are several entities with the same entity id.
    :type type: str
    :param attrs: Comma-separated list of attribute names whose data must be included in the response. The attributes are retrieved in the order specified by this parameter. If this parameter is not included, the attributes are retrieved in arbitrary order, and all the attributes of the entity are included in the response.
    :type attrs: str
    :param options: Options dictionary
    :type options: str

    :rtype: Entity
    """
    return 'do some magic!'


def retrieve_entity_attributes(entityId, type=None, attrs=None, options=None):  # noqa: E501
    """retrieve_entity_attributes

    This request is similar to retreiving the whole entity, however this one omits the &#x60;id&#x60; and &#x60;type&#x60; fields. Just like the general request of getting an entire entity, this operation must return only one entity element. If more than one entity with the same ID is found (e.g. entities with same ID but different type), an error message is returned, with the HTTP status code set to 409 Conflict. Response: * Successful operation uses 200 OK * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity to be retrieved
    :type entityId: str
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str
    :param attrs: Comma-separated list of attribute names whose data are to be included in the response. The attributes are retrieved in the order specified by this parameter. If this parameter is not included, the attributes are retrieved in arbitrary order, and all the attributes of the entity are included in the response.
    :type attrs: str
    :param options: Options dictionary
    :type options: str

    :rtype: Attribute
    """
    return 'do some magic!'


def update_existing_entity_attributes(entityId, body, type=None, options=None):  # noqa: E501
    """update_existing_entity_attributes

    The request payload is an object representing the attributes to update. The object follows the JSON entity Representation format (described in \&quot;JSON Entity Representation\&quot; section), except that &#x60;id&#x60; and &#x60;type&#x60; are not allowed. The entity attributes are updated with the ones in the payload. In addition to that, if one or more attributes in the payload doesn&#39;t exist in the entity, an error is returned. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity to be updated
    :type entityId: str
    :param body: JSON Attribute Representation
    :type body: dict | bytes
    :param type: Entity type, to avoid ambiguity in case there are several entities with the same entity id.
    :type type: str
    :param options: Operations options
    :type options: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = Attribute.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_or_append_entity_attributes(entityId, body, type=None, options=None):  # noqa: E501
    """update_or_append_entity_attributes

    The request payload is an object representing the attributes to append or update. The object follows the JSON entity Representation format (described in \&quot;JSON Entity Representation\&quot; section), except that &#x60;id&#x60; and &#x60;type&#x60; are not allowed. The entity attributes are updated with the ones in the payload, depending on whether the &#x60;append&#x60; operation option is used or not. * If &#x60;append&#x60; is not used: the entity attributes are updated (if they previously exist) or appended   (if they don&#39;t previously exist) with the ones in the payload. * If &#x60;append&#x60; is used (i.e. strict append semantics): all the attributes in the payload not   previously existing in the entity are appended. In addition to that, in case some of the   attributes in the payload already exist in the entity, an error is returned. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Entity id to be updated
    :type entityId: str
    :param body: JSON Attribute Representation
    :type body: dict | bytes
    :param type: Entity type, to avoid ambiguity in case there are several entities with the same entity id.
    :type type: str
    :param options: Operations options
    :type options: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = Attribute.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
