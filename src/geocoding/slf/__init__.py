"""
Support for working with NGSI Simple Location Format (SLF) data.
SLF is a lightweight format to represent simple 2D geometric figures such as
points, lines and polygons that is used to encode NGSI entity locations as well
as figures in NGSI geographical queries. You can read about it in the
*"Geospatial properties of entities"* and *"Geographical Queries"* sections of
the NGSI spec: http://fiware.github.io/specifications/ngsiv2/stable/.

Note that SLF uses the WGS84 coordinate system
(https://en.wikipedia.org/wiki/World_Geodetic_System#WGS84) and so points are
specified as ``(latitude, longitude)`` pairs whereas in GeoJSON the first
coordinate of a point is the longitude and the second is the latitude.


The ``geotypes`` module provides data types for all the SLF figures and the
``querytypes`` module builds on those types to provide data types to represent
NGSI geographical queries. The ``queryparser`` module provides parsing of NGSI
query strings into ASTs of SLF data types. The ``jsoncodec`` module serialises
SLF data type instances to GeoJSON whereas ``wktcodec`` serialises to WKT.
Additionally, the ``locparser`` module extracts location information from NGSI
entities to build SLF data type instances.

Below is bird-eye view of the components in the ``slf`` package.

.. image:: slf-components.png
"""


from .geotypes import *
from .jsoncodec import decode, encode
from .locparser import from_location_attribute
from .queryparser import from_geo_params
from .querytypes import *
from .wktcodec import encode_as_wkt
