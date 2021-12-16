from ld.utils import get_context, compute_attribute_mappings, extract_base_iris
from ld.cached_aiohttp import cached_aiohttp_document_loader
from pyld import jsonld


def test_ld_compacted(ngsi_ld):
    context = get_context(ngsi_ld)
    assert context == ['https://smartdatamodels.org/context.jsonld', 'https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld']
    mappings = compute_attribute_mappings(ngsi_ld, context)
    assert mappings['location'] == 'https://uri.etsi.org/ngsi-ld/location'
    assert mappings['controllingMethod'] == 'https://smart-data-models.github.io/data-models/terms.jsonld#/definitions/controllingMethod'


def test_ld_partially_expanded(ngsi_ld_partially_expanded):
    context = get_context(ngsi_ld_partially_expanded)
    assert context == 'https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.3.jsonld'
    mappings = compute_attribute_mappings(ngsi_ld_partially_expanded, context)
    assert mappings['name'] == 'https://uri.etsi.org/ngsi-ld/default-context/name'
    assert mappings['https://uri.fiware.org/ns/data-models#category'] == 'https://uri.fiware.org/ns/data-models#category'


def test_ld_expand_partially_expanded(ngsi_ld_partially_expanded):
    expanded = jsonld.expand(ngsi_ld_partially_expanded)
    assert expanded[0]['https://uri.etsi.org/ngsi-ld/default-context/name'] == [{'@type': ['https://uri.etsi.org/ngsi-ld/Property'],
      'https://uri.etsi.org/ngsi-ld/hasValue': [{'@value': 'Victory Farm'}]}]


def test_ld_context_cache(ngsi_ld):
    #TODO understand how to disable weird logs
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))
    expanded = jsonld.expand(ngsi_ld)
    assert expanded[0]['@type'] == ['https://uri.fiware.org/ns/data-models#Streetlight']


def test_extract_base_iris(ngsi_ld):
    expanded = jsonld.expand(ngsi_ld)
    iris = extract_base_iris(expanded)
    expected_iris = ['https://uri.etsi.org/ngsi-ld', 'http://www.w3.org/1999/02/22-rdf-syntax-ns', 'https://purl.org/geojson/vocab', 'https://uri.fiware.org/ns/data-models', 'https://schema.org', 'https://smart-data-models.github.io/data-models/terms.jsonld', 'https://uri.etsi.org/ngsi-ld/default-context']
    assert expected_iris == iris


def test_compress_using_base_iris(ngsi_ld):
    iris = extract_base_iris(jsonld.expand(ngsi_ld))
    compressed = jsonld.compact(ngsi_ld, iris)
    print(compressed)




