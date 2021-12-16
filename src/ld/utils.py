from pyld import jsonld
from urllib.parse import urlparse

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
        if (entry['subject']['type'] == 'IRI'):
            _proccess_iri(entry['subject']['value'], iris)
        if (entry['object']['type'] == 'IRI'):
            _proccess_iri(entry['object']['value'], iris)
        if (entry['predicate']['type'] == 'IRI'):
            _proccess_iri(entry['predicate']['value'], iris)
    return iris


def _proccess_iri(iri: str, list: list):
    if uri_validator(iri) and _base_iri(iri) not in list:
        list.append(_base_iri(iri))


def _base_iri(iri: str) -> str:
    if '#' in iri and iri.rindex("#") > 0:
        return iri[0:iri.rindex("#")]
    elif '/' in iri and iri.rindex("/") > 0 and iri.count("/") > 2:
        return iri[0:iri.rindex("/")]
    else:
        return iri


def uri_validator(iri):
    try:
        result = urlparse(iri)
        return all([result.scheme, result.netloc])
    except:
        return False