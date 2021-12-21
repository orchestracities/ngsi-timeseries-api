import sys
import logging
import dependency_injector.containers as containers
import dependency_injector.providers as providers
from utils.cfgreader import EnvReader, YamlReader, StrVar, MaybeString

class Log(containers.DeclarativeContainer):
    config = providers.Configuration(default={
        "target": "A",
        "items": {
            "A": {
                "option1": 60,
                "option2": 80,
            },
            "B": {
                "option1": 10,
                "option2": 20,
            },
        },
    })

    config_file = env_reader.read(StrVar(QL_DEFAULT_DB_ENV_VAR, None))

    config.from_yaml("config.local.yml", required=False)

    logging = providers.Resource(
        logging.basicConfig,
        stream=sys.stdout,
        level=config.log.level,
        format=config.log.format,
    )
