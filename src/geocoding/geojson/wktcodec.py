"""
This module provides functions to convert GeoJSON to/from WKT and WKB.
"""

from geomet import wkt, wkb
from typing import Optional


def encode_as_wkt(geo_json: dict, decimals: int = 16,
                  srid: Optional[int] = None) -> str:
    """
    Convert the given GeoJSON to WKT.

    :param geo_json: the GeoJSON data to convert.
    :param decimals: how many decimal digits to use for numbers, defaults to 16.
    :param srid: optional spatial reference system ID to include in the shape
        metadata. If given, prepend ``SRID=srid;`` to the WKT string. Notice
        that SRID isn't part of the WKT spec, but is an additional feature
        specified by OpenGIS. Keep this in mind when adding a SRID! Also notice
        that if the input GeoJSON already contains a SRID (``meta.srid`` or
        ``crs.properties.name`` property), that value will be used instead.
    :return: the corresponding WKT string.
    """
    wkt_shape = wkt.dumps(geo_json, decimals)
    if wkt_shape.lstrip().startswith('SRID'):
        return wkt_shape

    meta = f"SRID={srid};" if srid is not None else ''
    return meta + wkt_shape


def encode_as_wkb(geo_json: dict, big_endian=True) -> bytes:
    """
    Convert the given GeoJSON to WKB.

    :param geo_json: the GeoJSON data to convert.
    :param big_endian: endianness, defaults to big endian.
    :return: the corresponding WKB bytes.
    """
    return wkb.dumps(geo_json, big_endian)


def encode_as_wkb_hex(geo_json: dict, big_endian=True) -> str:
    """
    Convert the given GeoJSON to WKT.

    :param geo_json: the GeoJSON data to convert.
    :param big_endian: endianness, defaults to big endian.
    :return: the corresponding WKT string.
    """
    return encode_as_wkb(geo_json, big_endian).hex()


def decode_wkt(geom: str) -> dict:
    """
    Convert the given WKT geometry to GeoJSON.

    :param geom: the WKT geometry string.
    :return: the corresponding GeoJSON.
    """
    return wkt.loads(geom)


def decode_wkb(geom: bytes) -> dict:
    """
    Convert the given WKB geometry to GeoJSON.

    :param geom: the WKB geometry bytes.
    :return: the corresponding GeoJSON.
    """
    return wkb.loads(geom)


def decode_wkb_hexstr(geom: str) -> dict:
    """
    Convert the given WKB geometry to GeoJSON.

    :param geom: the WKB geometry as a HEX string.
    :return: the corresponding GeoJSON.
    """
    geom_bytes = bytes.fromhex(geom)
    geojson = decode_wkb(geom_bytes)
    if 'meta' in geojson:
        geojson.pop('meta')
    if 'crs' in geojson:
        geojson.pop('crs')
    return geojson


# TODO. Use shapely?
# Shapely seems to be a better library than GeoMet---see also notes about it
# in `slf.wktcodec`. In fact, I initially implemented and tested this with
# shapely---see implementation below. And it worked great until I had to
# build our QL Docker image which is based on Alpine Linux. Now, Shapely
# depends on GEOS, a geometry lib written in C/C++. Even though this is a
# widely used lib, Alpine support for it isn't quite there, see:
#
# * https://serverfault.com/questions/947044
# * https://stackoverflow.com/questions/39377911
#
# The workarounds suggested on the above pages didn't work for me. Also, it
# looks like now the lib is called geos in the Alpine packages and is only
# available in edge/testing.
# If Alpine GEOS support gets better in the future, we could ditch GeoMet
# and bring back Shapely...

# Shapely-based implementation of this module. (shapely = "~=1.6")

# import geojson
# import shapely.geometry
# import shapely.wkt
# import shapely.wkb
#
#
# def encode_as_wkt(geo_json: dict) -> str:
#     """
#     Convert the given GeoJSON to WKT.
#
#     :param geo_json: the GeoJSON data to convert.
#     :return: the corresponding WKT string.
#     """
#     return shapely.geometry.shape(geo_json).wkt
#
#
# def encode_as_wkb(geo_json: dict) -> bytes:
#     """
#     Convert the given GeoJSON to WKB.
#
#     :param geo_json: the GeoJSON data to convert.
#     :return: the corresponding WKB bytes.
#     """
#     return shapely.geometry.shape(geo_json).wkb
#
#
# def encode_as_wkb_hex(geo_json: dict) -> str:
#     """
#     Convert the given GeoJSON to WKT.
#
#     :param geo_json: the GeoJSON data to convert.
#     :return: the corresponding WKT string.
#     """
#     return shapely.geometry.shape(geo_json).wkb_hex
#
#
# def from_shapely_ast(ast) -> dict:
#     """
#     Convert the given Shapely AST into a GeoJSON dictionary.
#
#     :param ast: the AST.
#     :return: the dictionary.
#     """
#     geojson_str = geojson.dumps(ast)
#     return geojson.loads(geojson_str)
#
#
# def decode_wkt(geom: str) -> dict:
#     """
#     Convert the given WKT geometry to GeoJSON.
#
#     :param geom: the WKT geometry string.
#     :return: the corresponding GeoJSON.
#     """
#     ast = shapely.wkt.loads(geom)
#     return from_shapely_ast(ast)
#
#
# def decode_wkb(geom: bytes) -> dict:
#     """
#     Convert the given WKB geometry to GeoJSON.
#
#     :param geom: the WKB geometry bytes.
#     :return: the corresponding GeoJSON.
#     """
#     ast = shapely.wkb.loads(geom)
#     return from_shapely_ast(ast)
#
#
# def decode_wkb_hexstr(geom: str) -> dict:
#     """
#     Convert the given WKB geometry to GeoJSON.
#
#     :param geom: the WKB geometry as a HEX string.
#     :return: the corresponding GeoJSON.
#     """
#     ast = shapely.wkb.loads(geom, hex=True)
#     return from_shapely_ast(ast)
