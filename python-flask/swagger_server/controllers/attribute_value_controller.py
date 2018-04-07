import connexion
import six

from swagger_server.models.attribute_value import AttributeValue  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server import util


def get_attribute_value(entityId, attrName, type=None):  # noqa: E501
    """get_attribute_value

    This operation returns the &#x60;value&#x60; property with the value of the attribute. * If attribute value is JSON Array or Object:   * If &#x60;Accept&#x60; header can be expanded to &#x60;application/json&#x60; or &#x60;text/plain&#x60; return the value as a JSON with a     response type of application/json or text/plain (whichever is the first in &#x60;Accept&#x60; header or     &#x60;application/json&#x60; in the case of &#x60;Accept: */*&#x60;).   * Else return a HTTP error \&quot;406 Not Acceptable: accepted MIME types: application/json, text/plain\&quot; * If attribute value is a string, number, null or boolean:   * If &#x60;Accept&#x60; header can be expanded to text/plain return the value as text. In case of a string, citation     marks are used at the begining and end.   * Else return a HTTP error \&quot;406 Not Acceptable: accepted MIME types: text/plain\&quot; Response: * Successful operation uses 200 OK. * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity in question
    :type entityId: str
    :param attrName: Name of the attribute to be retrieved.
    :type attrName: str
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str

    :rtype: AttributeValue
    """
    return 'do some magic!'


def update_attribute_value(entityId, attrName, body, type=None):  # noqa: E501
    """update_attribute_value

    The request payload is the new attribute value. * If the request payload MIME type is &#x60;application/json&#x60;, then the value of the attribute is set to   the JSON object or array coded in the payload (if the payload is not a valid JSON document,   then an error is returned). * If the request payload MIME type is &#x60;text/plain&#x60;, then the following algorithm is applied to the   payload:   * If the payload starts and ends with citation-marks (&#x60;\&quot;&#x60;), the value is taken as a string     (the citation marks themselves are not considered part of the string)   * If &#x60;true&#x60; or &#x60;false&#x60;, the value is taken as a boolean.   * If &#x60;null&#x60;, the value is taken as null.   * If these first three tests &#39;fail&#39;, the text is interpreted as a number.   * If not a valid number, then an error is returned and the attribute&#39;s value is unchanged. The payload MIME type in the request is specified in the &#x60;Content-Type&#x60; HTTP header. Response: * Successful operation uses 204 No Content * Errors use a non-2xx and (optionally) an error payload. See subsection on \&quot;Error Responses\&quot; for   more details. # noqa: E501

    :param entityId: Id of the entity to be updated.
    :type entityId: str
    :param attrName: Attribute name.
    :type attrName: str
    :param body: JSON AttributeValue Representation
    :type body: dict | bytes
    :param type: Entity type, to avoid ambiguity in the case there are several entities with the same entity id.
    :type type: str

    :rtype: None
    """
    if connexion.request.is_json:
        body = AttributeValue.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
