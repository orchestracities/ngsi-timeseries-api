import logging
import os

from utils.cfgreader import EnvReader, BoolVar, IntVar


class SQLTranslatorConfig:
    """
    Provide access to SQL Translator config values.
    """

    def __init__(self, env: dict = os.environ):
        self.store = EnvReader(var_store=env,
                               log=logging.getLogger(__name__).info)

    def default_limit(self) -> int:
        fallback_limit = 10000
        var = IntVar('DEFAULT_LIMIT', default_value=fallback_limit)
        return self.store.safe_read(var)

    def keep_raw_entity(self) -> bool:
        var = BoolVar('KEEP_RAW_ENTITY', False)
        return self.store.safe_read(var)
