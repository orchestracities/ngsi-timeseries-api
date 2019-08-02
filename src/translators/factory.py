import yaml
import os

from translators.crate import CrateTranslatorInstance
from translators.timescale import postgres_translator_instance
from utils.jsondict import maybe_string_match


CRATE_BACKEND = 'crate'
TIMESCALE_BACKEND = 'timescale'

QL_CONFIG_ENV_VAR = 'QL_CONFIG'


def read_config() -> dict:
    path = os.environ.get(QL_CONFIG_ENV_VAR)
    if path:
        file = open(path)
        return yaml.safe_load(file)
    return {}


def translator_for(fiware_service: str):
    config = read_config()
    backend = maybe_string_match(config, 'tenants', fiware_service, 'backend')\
        or maybe_string_match(config, 'default-backend')
    backend = backend.strip().lower() if backend is not None else ''

    if backend == CRATE_BACKEND:
        return CrateTranslatorInstance()
    if backend == TIMESCALE_BACKEND:
        return postgres_translator_instance()
    return CrateTranslatorInstance()
