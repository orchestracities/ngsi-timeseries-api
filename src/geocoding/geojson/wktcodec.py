"""
This module provides functions to convert GeoJSON to/from WKT and WKB.
"""

import geojson
import shapely.geometry
import shapely.wkt
import shapely.wkb


def encode_as_wkt(geo_json: dict) -> str:
    """
    Convert the given GeoJSON to WKT.

    :param geo_json: the GeoJSON data to convert.
    :return: the corresponding WKT string.
    """
    return shapely.geometry.shape(geo_json).wkt


def encode_as_wkb(geo_json: dict) -> bytes:
    """
    Convert the given GeoJSON to WKB.

    :param geo_json: the GeoJSON data to convert.
    :return: the corresponding WKB bytes.
    """
    return shapely.geometry.shape(geo_json).wkb


def encode_as_wkb_hex(geo_json: dict) -> str:
    """
    Convert the given GeoJSON to WKT.

    :param geo_json: the GeoJSON data to convert.
    :return: the corresponding WKT string.
    """
    return shapely.geometry.shape(geo_json).wkb_hex


def from_shapely_ast(ast) -> dict:
    """
    Convert the given Shapely AST into a GeoJSON dictionary.

    :param ast: the AST.
    :return: the dictionary.
    """
    geojson_str = geojson.dumps(ast)
    return geojson.loads(geojson_str)


def decode_wkt(geom: str) -> dict:
    """
    Convert the given WKT geometry to GeoJSON.

    :param geom: the WKT geometry string.
    :return: the corresponding GeoJSON.
    """
    ast = shapely.wkt.loads(geom)
    return from_shapely_ast(ast)


def decode_wkb(geom: bytes) -> dict:
    """
    Convert the given WKB geometry to GeoJSON.

    :param geom: the WKB geometry bytes.
    :return: the corresponding GeoJSON.
    """
    ast = shapely.wkb.loads(geom)
    return from_shapely_ast(ast)


def decode_wkb_hexstr(geom: str) -> dict:
    """
    Convert the given WKB geometry to GeoJSON.

    :param geom: the WKB geometry as a HEX string.
    :return: the corresponding GeoJSON.
    """
    ast = shapely.wkb.loads(geom, hex=True)
    return from_shapely_ast(ast)
