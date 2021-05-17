import logging
from dependency_injector import containers, providers

class SLogger(logging.Logger):
    def __init__(self, level='INFO'):
        super().__init__('clone_replica_controller')
        self.setLevel(level)
        c_handler = logging.StreamHandler()
        c_handler.setLevel(level)
        c_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s:%(levelname)s:%(message)s'))
        self.addHandler(c_handler)


class LoggerContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    logger_svc = providers.Singleton(
        SLogger,
        config.loglevel
    )


