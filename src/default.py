VERSION = '0.9.0-dev'

DESCRIPTION = "QuantumLeap: timeseries for NGSIv2 and NGSI-LD (experimental)"

CONTACT = {
        "name": "Martel Innovate",
        "url": "https://www.martel-innovate.com",
        "email": "info@orchestracities.com",
    }

LICENSE = {
       "name": "MIT",
       "url": "https://github.com/orchestracities/ngsi-timeseries-api/blob/master/LICENSE",
    }


TAGS = [
    {
        "name": "meta",
    },
    {
        "name": "v2",
    },
    {
        "name": "ngsi-ld",
    },
]

# NGSI TYPES
# The types are based on Orion implementation.
# Specs don't provide much details.

NGSI_DATETIME = 'DateTime'
NGSI_ID = 'id'
NGSI_GEOJSON = 'geo:json'
NGSI_LD_GEOMETRY = 'GeoProperty'
NGSI_GEOPOINT = 'geo:point'
NGSI_ISO8601 = 'ISO8601'
NGSI_STRUCTURED_VALUE = 'StructuredValue'
NGSI_TEXT = 'Text'
NGSI_TYPE = 'type'

# Name of the attribute where the temporal index will be stored
TIME_INDEX_NAME = 'time_index'
