"""
Utils to stream Pydantic models as JSON data in Flask responses.
"""
from typing import Iterable

from flask import Response
from pydantic import BaseModel


def json_array_streamer(xs: Iterable[BaseModel]) -> Iterable[str]:
    yield '[\n'
    for x in xs:
        json_repr = x.json()
        yield json_repr + ',\n'
    yield 'null\n]'
# TODO how to get rid of the null terminator in an efficient and **simple**
# way? I could use the same put-back approach as in itersplit but I'd rather
# keep it simple.


def build_json_array_response_stream(xs: Iterable[BaseModel]) -> Response:
    """
    Build a 200 response to stream the input data to the client.
    Each input Pydantic model gets converted to JSON and written to the
    response buffer immediately to avoid having to materialise the whole
    input iterable in memory. So if the input is actually a generator,
    we'll send data to the client in constant space.

    :param xs: the Pydantic models to return to the client.
    :return: a Flask JSON response containing an array of JSON objects.
    """
    return Response(json_array_streamer(xs), mimetype='application/json')
