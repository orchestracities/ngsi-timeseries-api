from pyld import jsonld
from ld.cached_aiohttp import cached_aiohttp_document_loader

jsonld.set_document_loader(cached_aiohttp_document_loader(timeout=30))

doc = {
    "id": "urn:ngsi-ld:Streetlight:streetlight:guadalajara:4567",
    "type": "Streetlight",
    "location": {
        "type": "GeoProperty",
        "value": {
            "type": "Point",
            "coordinates": [
                -3.164485591715449,
                40.62785133667262
            ]
        }
    },
    "areaServed": {
        "type": "Property",
        "value": "Roundabouts city entrance"
    },
    "status": {
        "type": "Property",
        "value": "ok"
    },
    "refStreetlightGroup": {
        "type": "Relationship",
        "object": "urn:ngsi-ld:StreetlightGroup:streetlightgroup:G345"
    },
    "refStreetlightModel": {
        "type": "Relationship",
        "object": "urn:ngsi-ld:StreetlightModel:streetlightmodel:STEEL_Tubular_10m"
    },
    "circuit": {
        "type": "Property",
        "value": "C-456-A467"
    },
    "lanternHeight": {
        "type": "Property",
        "value": 10
    },
    "locationCategory": {
        "type": "Property",
        "value": "centralIsland"
    },
    "powerState": {
        "type": "Property",
        "value": "off"
    },
    "controllingMethod": {
        "type": "Property",
        "value": "individual"
    },
    "dateLastLampChange": {
        "type": "Property",
        "value": {
            "@type": "DateTime",
            "@value": "2016-07-08T08:02:21.753Z"
        }
    },
    "@context": [
        "https://smartdatamodels.org/context.jsonld",
        "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
    ]
}


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
        uri, value = expand_attribute(key, doc[key], context)
        mapping[key] = uri
    return mapping


context = get_context(doc)
compacted = jsonld.compact(doc, context)
mappings = compute_attribute_mappings(compacted, context)

for key, value in mappings.items():
    print(key + "--->" + value)
