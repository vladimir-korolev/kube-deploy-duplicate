# It is not neccessary for the current task
# but this implementation allows has multiple configmap (if selector and merge configmap are implemnted)
# and it's a best practice to use crd with kubernetes operator


from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide

from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger

class AKubeCrd(ABC):
    @abstractmethod
    def getInitConfigCrd(self):
        pass

class KubeCrd(AKubeCrd):
    CRD_GROUP = 'crds.grove'
    CRD_VERSION = 'v1'
    CRD_PLURAL = 'ddprofcrds'

    def __init__(self, name, namespace):
        self._setLogger()
        self._setKubeEngine()
        self._name = name
        self._namespace = namespace

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    @inject
    def _setKubeEngine(self, engine: KubeEngine = Provide[EngineContainer.kube_engine]):
        self._kube_engine = engine

    def getInitConfigCrd(self):
        return self._kube_engine.getCrd(KubeCrd.CRD_GROUP, KubeCrd.CRD_VERSION, self._namespace, KubeCrd.CRD_PLURAL, self._name)

