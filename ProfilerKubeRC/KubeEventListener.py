from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide

import threading

from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger


lock = threading.Lock()


class KubeEventListenerInterface(ABC):

    @abstractmethod
    def runWatcher(self):
        pass

    @abstractmethod
    def addEventHandler(self, handler):
        pass

# The interface for interacting with listener
# - eventHandler: This method should be called from listener as a callback call
# - update: to do steps to update object's configuration
class KubeEventHandlerInterface(ABC):

    @abstractmethod
    def eventHandler(self, event):
        pass

    @abstractmethod
    def update(self):
        pass

class AKubeEventListener(ABC):

    @abstractmethod
    def update(self, event):
        pass

    @abstractmethod
    def addEventHandler(self, listener: KubeEventHandlerInterface):
        pass


class KubeEventListener(AKubeEventListener):

    def __init__(self, namespace):
        self._setLogger()
        self._namespace = namespace
        self._event_listeners = []
        self._setKubeEngine()

    @inject
    def _setKubeEngine(self, engine: KubeEngine = Provide[EngineContainer.kube_engine]):
        self._kube_engine = engine

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    def addEventHandler(self, listener: KubeEventHandlerInterface):
        self._event_listeners.append(listener)

    def update(self, event):
        pass


class KubeDeploymentEventListener(KubeEventListener):

    def runWatcher(self):
        try:
            self._kube_engine.watchDeployments(self._namespace, self.update)
        except Exception as e:
            self._logger.exception(e)

    def update(self, event):
        with lock:
            self._logger.debug("Updating deployments")
            for deploy in self._event_listeners:
                deploy.eventHandler(event)


class KubeCmEventListener(KubeEventListener):

    def runWatcher(self):
        try:
            self._kube_engine.watchConfigMaps(self._namespace, self.update)
        except Exception as e:
            self._logger.exception(e)

    def update(self, event):
        with lock:
            self._logger.debug("Updating configmaps")
            for cm in self._event_listeners:
                cm.eventHandler(event)
