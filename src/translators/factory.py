import logging
import os
import yaml

from translators.crate import CrateTranslatorInstance
from translators.timescale import postgres_translator_instance
from utils.jsondict import maybe_string_match


CRATE_BACKEND = 'crate'
TIMESCALE_BACKEND = 'timescale'

QL_CONFIG_ENV_VAR = 'QL_CONFIG'


def log():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def read_config() -> dict:
    path = os.environ.get(QL_CONFIG_ENV_VAR)
    if path:
        log().info(f"using config file: {path}")
        file = open(path)
        return yaml.safe_load(file)

    log().info(f"no config file specified, using defaults.")
    return {}


def translator_for(fiware_service: str):
    config = read_config()
    backend = maybe_string_match(config, 'tenants', fiware_service, 'backend')\
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
