from pyld import jsonld


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
