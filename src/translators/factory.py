import logging
from translators.crate import CrateTranslatorInstance
from translators.timescale import postgres_translator_instance
from utils.cfgreader import EnvReader, YamlReader, StrVar, MaybeString
from utils.jsondict import maybe_string_match


CRATE_BACKEND = 'crate'
TIMESCALE_BACKEND = 'timescale'

QL_CONFIG_ENV_VAR = 'QL_CONFIG'

QL_DEFAULT_DB_ENV_VAR = 'QL_DEFAULT_DB'


def log():
    return logging.getLogger(__name__)


def lookup_backend(fiware_service: str) -> MaybeString:
    cfg_reader = YamlReader(log=log().debug)
    env_reader = EnvReader(log=log().info)

    config = cfg_reader.from_env_file(QL_CONFIG_ENV_VAR, defaults={})
    tenant_backend = maybe_string_match(config, 'tenants', fiware_service,
                                        'backend')
    default_backend = maybe_string_match(config, 'default-backend')

    env_backend = env_reader.read(StrVar(QL_DEFAULT_DB_ENV_VAR, CRATE_BACKEND))

    return tenant_backend or env_backend or default_backend


def translator_for(fiware_service: str):
    backend = lookup_backend(fiware_service)
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
