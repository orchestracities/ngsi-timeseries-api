"""
Support for working with NGSI Simple Location Format (SLF) data.
SLF is a lightweight format to represent simple 2D geometric figures such as
points, lines and polygons that is used to encode NGSI entity locations as well
as figures in NGSI geographical queries.

The ``geotypes`` module provides data types for all the SLF figures and the
``querytypes`` module builds on those types to provide data types to represent
NGSI geographical queries. The ``queryparser`` module provides parsing of NGSI
query strings into ASTs of SLF data types whereas the ``jsoncodec`` module
serialises SLF data type instances to GeoJSON. Additionally, the ``locparser``
module extracts location information from NGSI entities to build SLF data type
instances.

Below is bird-eye view of the components in the ``slf`` package.

.. image:: slf-components.png
"""


from .geotypes import *
from .jsoncodec import encode
from .locparser import from_location_attribute
from .queryparser import from_geo_params
from .querytypes import *
