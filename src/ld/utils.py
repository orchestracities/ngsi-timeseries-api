import string
import random

from pyld import jsonld
from urllib.parse import urlparse

from pyld.jsonld import JsonLdProcessor, ContextResolver


def default_context() -> str:
    return "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"


def default_processor_options() -> dict:
    options = {}
    options.setdefault('base', '')
    options.setdefault('compactArrays', True)
    options.setdefault('graph', False)
    options.setdefault('skipExpansion', False)
    options.setdefault('activeCtx', False)
    options.setdefault('documentLoader', jsonld.get_document_loader())
    options.setdefault('contextResolver',
                       ContextResolver(jsonld._resolved_context_cache,
                                       options['documentLoader']))
    options.setdefault('extractAllScripts', False)
    options.setdefault('processingMode', 'json-ld-1.1')
    options.setdefault('link', False)
    return options


def get_context(doc: dict) -> dict:
    if doc and '@context' in doc:
        return doc['@context']
    else:
        return {}


def expand_attribute(name: str, value: any, context: dict) -> (str, dict):
    attr = {
        name: value,
        '@context': context
    }
    expanded = jsonld.expand(attr)
    for item in expanded:
        for uri in item.keys():
            return uri, item[uri]
    return name, value


def compute_attribute_mappings(compacted: dict, context: dict) -> dict:
    mapping = {}
    for key in compacted:
        uri, value = expand_attribute(key, compacted[key], context)
        mapping[key] = uri
    return mapping


def extract_base_iris(expanded: dict) -> list:
    iris = []
    rdf = jsonld.to_rdf(expanded)
    for entry in rdf['@default']:
        if entry['subject']['type'] == 'IRI':
            base_iri = _base_iri(entry['subject']['value'])
            if base_iri and base_iri not in iris:
                iris.append(base_iri)
        if entry['object']['type'] == 'IRI':
            base_iri = _base_iri(entry['object']['value'])
            if base_iri and base_iri not in iris:
                iris.append(base_iri)
        if entry['predicate']['type'] == 'IRI':
            base_iri = _base_iri(entry['predicate']['value'])
            if base_iri and base_iri not in iris:
                iris.append(base_iri)
    return iris


def compute_mappings(context: dict, filter: dict or None = None) -> dict:
    processor = JsonLdProcessor()
    active_ctx = processor._get_initial_context(default_processor_options())
    context = processor.process_context(
        active_ctx, context, default_processor_options())
    mappings = {}
    reverse_mappings = {}
    for key in context['mappings'].keys():
        if filter and key in filter.keys():
            mappings[key] = context['mappings'][key]['@id']
            reverse_mappings[context['mappings'][key]['@id']] = key
        if not filter:
            mappings[key] = context['mappings'][key]['@id']
            reverse_mappings[context['mappings'][key]['@id']] = key
    return mappings, reverse_mappings


def combine_mappings(mappings_1: dict, mappings_2: dict) -> dict:
    mappings = mappings_1.copy()
    for key in mappings_2.keys():
        if key in mappings_1.keys(
        ) and mappings_1[key] != mappings_2[key] and mappings_2[key] not in mappings_1.values():
            new_key = generate_random_string(mappings.keys())
            mappings[new_key] = mappings_2[key]
    return mappings


def generate_random_string(invalid: list, length: int = 10) -> str:
    letters = string.ascii_lowercase
    temp_key = ''.join(random.choice(letters) for i in range(length))
    while temp_key in invalid:
        temp_key = ''.join(random.choice(letters) for i in range(length))
    return temp_key


def _base_iri(iri: str) -> str:
    if uri_validator(iri):
        if '#' in iri and iri.rindex("#") > 0:
            if '/' not in iri or iri.rindex("#") > iri.rindex("/"):
                return iri[0:iri.rindex("#") + 1]
        if '/' in iri and iri.rindex("/") > 0 and iri.count("/") > 2:
            if '#' not in iri or iri.rindex("#") < iri.rindex("/"):
                return iri[0:iri.rindex("/") + 1]
        return iri
    return None


def uri_validator(iri):
    try:
        result = urlparse(iri)
        return all([result.scheme, result.netloc])
    except BaseException:
        return False
