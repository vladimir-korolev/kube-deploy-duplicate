import sys, os

from ProfilerKubeRC.KubeEventListener import KubeEventListener
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.ServiceInit import ServiceInit
from ProfilerKubeRC.logger import LoggerContainer
from dependency_injector.wiring import Provide
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.KubeConfigMap import KubeConfigMap
from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.KubeDeployment import KubeDeploymentWithClone
from ProfilerKubeRC.KubeClient import KubeClient
from ProfilerKubeRC.KubeEKSClusterInfo import KubeEKSClusterInfo
from ProfilerKubeRC.KubeCrd import KubeCrd

logger: SLogger = Provide[LoggerContainer.logger_svc]

if __name__ == '__main__':

    logger_container = LoggerContainer()
    logger_container.config.loglevel.from_env('LOGLEVEL')
    logger_container.wire(modules=[sys.modules[__name__]])

    logger.info("Starting application")

    engine_container = EngineContainer()
    engine_container.config.api_key.from_env('API_KEY')
    engine_container.config.timeout.from_env('TIMEOUT')
    engine_container.config.cluster_type.from_env('CLIENT')
    engine_container.config.cluster.from_env('CLUSTER')
    engine_container.config.region.from_env('REGION')
    # engine_container.config.crd_name.from_env('CRD_NAME')
    # engine_container.config.cm_namespace.from_env('CM_NAMESPACE')
    engine_container.wire(modules=[sys.modules[__name__]])
    # engine_container.config.namesuffix.from_env('NAMESUFFIX')

    crdConfig = os.environ.get('CRD_NAME', 'profiler-deployment')
    crdNamespace = os.environ.get('CRD_NAMESPACE', 'default')

    services = ServiceInit(crdConfig, crdNamespace)
    services.runInit()
    services.runListeners()

