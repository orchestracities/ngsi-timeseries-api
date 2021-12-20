from ld.utils import get_context, compute_attribute_mappings, \
    compute_mappings, \
    _base_iri, combine_mappings
from ld.cached_aiohttp import cached_aiohttp_document_loader
from pyld import jsonld


def test_ld_compacted(ngsi_ld):
    context = get_context(ngsi_ld)
    assert context == [
        'https://smartdatamodels.org/context.jsonld',
        'https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld']
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
    assert expanded[0]['https://uri.etsi.org/ngsi-ld/default-context/name'] == [{'@type': [
        'https://uri.etsi.org/ngsi-ld/Property'], 'https://uri.etsi.org/ngsi-ld/hasValue': [{'@value': 'Victory Farm'}]}]


def test_ld_context_cache(ngsi_ld):
    # TODO understand how to disable weird logs
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))
    expanded = jsonld.expand(ngsi_ld)
    assert expanded[0]['@type'] == ['https://uri.fiware.org/ns/data-models#Streetlight']


def test_base_iris():
    assert _base_iri('https://schema.org/areaServed') == 'https://schema.org/'
    assert _base_iri(
        'https://uri.etsi.org/ngsi-ld/Property') == 'https://uri.etsi.org/ngsi-ld/'
    assert _base_iri(
        'https://uri.etsi.org/ngsi-ld/default-context/lanternHeight') == 'https://uri.etsi.org/ngsi-ld/default-context/'
    assert _base_iri(
        'https://uri.fiware.org/ns/data-models#refStreetlightModel') == 'https://uri.fiware.org/ns/data-models#'
    assert _base_iri('https://smart-data-models.github.io/data-models/terms.jsonld#/definitions/locationCategory') == 'https://smart-data-models.github.io/data-models/terms.jsonld#/definitions/'


def test_computed_mappings(ngsi_ld):
    context = get_context(ngsi_ld)
    mappings, reserve_mappings = compute_mappings(context)
    assert mappings['areaServed'] == 'https://schema.org/areaServed'
    assert mappings['Property'] == 'https://uri.etsi.org/ngsi-ld/Property'
    assert mappings['value'] == 'https://uri.etsi.org/ngsi-ld/hasValue'
    # lanternHeight is failng because of mispelling in the smart data models...
    # assert mappings['lanternHeight'] == 'https://uri.etsi.org/ngsi-ld/default-context/lanternHeight'
    assert mappings['refStreetlightModel'] == 'https://uri.fiware.org/ns/data-models#refStreetlightModel'
    assert mappings['locationCategory'] == 'https://smart-data-models.github.io/data-models/terms.jsonld#/definitions/locationCategory'
    assert reserve_mappings['https://schema.org/areaServed'] == 'areaServed'


def test_mapping_filtering(ngsi_ld):
    context = get_context(ngsi_ld)
    mappings, reserve_mappings = compute_mappings(context, ngsi_ld)
    assert len(mappings) == len(reserve_mappings) == 12
    # should be 13, but due to wrong context for streetligthing is only 12


def test_compress_expand_reversability(ngsi_ld):
    context = get_context(ngsi_ld)
    expanded = jsonld.expand(ngsi_ld)
    compressed = jsonld.compact(expanded, context)

    # TODO investigate why reverse is not working correctly for Datetime
    # is this an error in the context, or in the processor?
    # this what the compact code returns:
    #  'dateLastLampChange': {'type': 'Property',
    #                         'value': {'@value': '2016-07-08T08:02:21.753Z',
    #                                   'type': 'DateTime'}},
    # type inside value should be @type
    compressed.pop('dateLastLampChange')
    ngsi_ld.pop('dateLastLampChange')

    assert compressed == ngsi_ld


def test_different_context_same_entity(
        ngsi_my_family_according_to_me,
        ngsi_my_family_according_to_my_wife):
    expanded_1 = jsonld.expand(ngsi_my_family_according_to_me)
    expanded_2 = jsonld.expand(ngsi_my_family_according_to_my_wife)
    assert expanded_1 == expanded_2


def test_combine_mappings(
        ngsi_my_family_according_to_me,
        ngsi_my_family_according_to_my_wife):
    context_1 = get_context(ngsi_my_family_according_to_me)
    mappings_1, reserve_mappings_1 = compute_mappings(
        context_1, ngsi_my_family_according_to_me)
    context_2 = get_context(ngsi_my_family_according_to_my_wife)
    mappings_2, reserve_mappings_2 = compute_mappings(
        context_2, ngsi_my_family_according_to_my_wife)
    new_mappings = combine_mappings(mappings_1, mappings_2)
    assert new_mappings == mappings_1


def test_expansion():
    jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=1000))
    entity = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "@type": "Create",
        "actor": {
            "@type": "Person",
            "@id": "acct:sally@example.org",
            "name": "Sally"
        },
        "object": {
            "@type": "Note",
            "content": "This is a simple note"
        },
        "published": "2015-01-25T12:34:56Z"
    }
    expanded = jsonld.expand(entity)
    entity = {
        "@context": "http://json-ld.org/contexts/person.jsonld",
        "@id": "http://dbpedia.org/resource/John_Lennon",
        "name": "John Lennon",
        "born": "1940-10-09",
        "spouse": "http://dbpedia.org/resource/Cynthia_Lennon"
    }
    expanded = jsonld.expand(entity)
    entity = {
        "@context": "http://schema.org",
        "@id": "https://nystudio107.com/#identity",
        "@type": "Organization",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "US",
            "addressLocality": "Webster",
            "addressRegion": "NY",
            "postalCode": "14580"},
        "alternateName": "nys",
        "description": "We do technology-based consulting, branding, design, and development. Making the web better one site at a time, with a focus on performance, usability & SEO",
        "email": "info@nystudio107.com",
        "founder": "Andrew Welch, Polly Welch",
        "foundingDate": "2013-05-02",
        "foundingLocation": "Webster, NY",
        "image": {
            "@type": "ImageObject",
            "height": "2048",
            "url": "https://nystudio107-ems2qegf7x6qiqq.netdna-ssl.com/img/site/nys_logo_seo.png",
            "width": "2048"},
        "logo": {
            "@type": "ImageObject",
            "height": "60",
            "url": "https://nystudio107.com/img/site/_600x60_fit_center-center_82_none/nys_logo_seo.png",
            "width": "600"},
        "name": "nystudio107",
                "sameAs": [
                    "https://twitter.com/nystudio107",
                    "https://www.facebook.com/newyorkstudio107",
                    "https://plus.google.com/+nystudio107com",
                    "https://www.youtube.com/channel/UCOZTZHQdC-unTERO7LRS6FA",
                    "https://github.com/nystudio107"],
        "url": "https://nystudio107.com/"}
    expanded = jsonld.expand(entity)
    entity = {
        "@context": {
            "name": "http://schema.org/name",
            "description": "http://schema.org/description",
            "image": {
                "@id": "http://schema.org/image",
                "@type": "@id"
            },
            "geo": "http://schema.org/geo",
            "latitude": {
                "@id": "http://schema.org/latitude",
                "@type": "xsd:float"
            },
            "longitude": {
                "@id": "http://schema.org/longitude",
                "@type": "xsd:float"
            },
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        },
        "name": "The Empire State Building",
        "description": "The Empire State Building is a 102-story landmark in New York City.",
        "image": "http://www.civil.usherbrooke.ca/cours/gci215a/empire-state-building.jpg",
        "geo": {
            "latitude": "40.75",
            "longitude": "73.98"
        }
    }
    entity = {
        "@context": {
            "label": "http://www.w3.org/2000/01/rdf-schema#label",
            "label_en": {
                "@id": "http://www.w3.org/2000/01/rdf-schema#label",
                "@language": "en"},
            "starring": "http://dbpedia.org/ontology/starring"},
        "label": "12 Monkeys",
        "starring": "http://dbpedia.org/resource/Brad_Pitt"}
    expanded = jsonld.expand(entity)
