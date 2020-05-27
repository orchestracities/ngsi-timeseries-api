import logging
import os
from translators.crate import CrateTranslatorInstance
from translators.timescale import postgres_translator_instance
from utils.cfgreader import YamlReader
from utils.jsondict import maybe_string_match


CRATE_BACKEND = 'crate'
TIMESCALE_BACKEND = 'timescale'

QL_CONFIG_ENV_VAR = 'QL_CONFIG'

QL_DEFAULT_DB_ENV_VAR = 'QL_DEFAULT_DB'


def log():
    return logging.getLogger(__name__)


def translator_for(fiware_service: str):
    reader = YamlReader(log=log().debug)
    config = reader.from_env_file(QL_CONFIG_ENV_VAR, defaults={})

    backend = maybe_string_match(config, 'tenants', fiware_service, 'backend')\
        or os.environ.get(QL_DEFAULT_DB_ENV_VAR, 'crate')\
        or maybe_string_match(config, 'default-backend')
    backend = backend.strip().lower() if backend is not None else ''

    if backend == CRATE_BACKEND:
        translator = CrateTranslatorInstance()
        selected = CRATE_BACKEND
    elif backend == TIMESCALE_BACKEND:
        translator = postgres_translator_instance()
        selected = TIMESCALE_BACKEND
    else:
        translator = CrateTranslatorInstance()
        selected = CRATE_BACKEND

    log().info(
        f"Backend selected for tenant '{fiware_service}' is: {selected}")
    return translator
