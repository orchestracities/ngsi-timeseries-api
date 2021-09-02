import logging
import os

from utils.cfgreader import EnvReader, BoolVar, IntVar


DEFAULT_LIMIT_VAR = 'DEFAULT_LIMIT'
KEEP_RAW_ENTITY_VAR = 'KEEP_RAW_ENTITY'
FALLBACK_LIMIT = 10000


class SQLTranslatorConfig:
    """
    Provide access to SQL Translator config values.
    """

    def __init__(self, env: dict = os.environ):
        self.store = EnvReader(var_store=env,
                               log=logging.getLogger(__name__).debug)

    def default_limit(self) -> int:
        var = IntVar(DEFAULT_LIMIT_VAR, default_value=FALLBACK_LIMIT)
        return self.store.safe_read(var)

    def keep_raw_entity(self) -> bool:
        var = BoolVar(KEEP_RAW_ENTITY_VAR, False)
        return self.store.safe_read(var)
