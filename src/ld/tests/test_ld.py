from ld.utils import get_context, compute_attribute_mappings
from ld.cached_aiohttp import cached_aiohttp_document_loader
from pyld import jsonld


def test_ld_compacted(ngsi_ld):
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))
    context = get_context(ngsi_ld)
    assert context == ['https://smartdatamodels.org/context.jsonld', 'https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld']
    mappings = compute_attribute_mappings(ngsi_ld, context)
    assert mappings['location'] == 'https://uri.etsi.org/ngsi-ld/location'
    assert mappings['controllingMethod'] == 'https://smart-data-models.github.io/data-models/terms.jsonld#/definitions/controllingMethod'


def test_ld_partially_expanded(ngsi_ld_partially_expanded):
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))
    context = get_context(ngsi_ld_partially_expanded)
    assert context == 'https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.3.jsonld'
    mappings = compute_attribute_mappings(ngsi_ld_partially_expanded, context)
    assert mappings['name'] == 'https://uri.etsi.org/ngsi-ld/default-context/name'
    assert mappings['https://uri.fiware.org/ns/data-models#category'] == 'https://uri.fiware.org/ns/data-models#category'


def test_ld_expand_partially_expanded(ngsi_ld_partially_expanded):
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))
    expanded = jsonld.expand(ngsi_ld_partially_expanded)
    print(expanded)









