import sys, os

import ProfilerKubeRC

from ProfilerKubeRC.container import EngineContainer, TasksContainer
from ProfilerKubeRC.ServiceInit import ServiceInit
from ProfilerKubeRC.logger import LoggerContainer
from dependency_injector.wiring import Provide
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.KubeEventListener import KubeEventListener
from ProfilerKubeRC.KubeConfigMap import KubeConfigMap
from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.KubeDeployment import KubeDeploymentWithClone
from ProfilerKubeRC.KubeClient import KubeClient
from ProfilerKubeRC.KubeEKSClusterInfo import KubeEKSClusterInfo
from ProfilerKubeRC.KubeCrd import KubeCrd
from ProfilerKubeRC.ServiceInit import ServiceInit
from ProfilerKubeRC.TasksManager import TasksManager
from ProfilerKubeRC.healthcheck import HealthCheck
from ProfilerKubeRC.runApp import startReplicationController

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
    engine_container.wire(modules=[sys.modules[__name__]])

    tasks_container = TasksContainer()
    tasks_container.wire(modules=[sys.modules[__name__]])

    crdConfig = os.environ.get('CRD_NAME', 'profiler-deployment')
    crdNamespace = os.environ.get('CRD_NAMESPACE', 'default')
    startReplicationController()