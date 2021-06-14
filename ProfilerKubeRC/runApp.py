import sys, os
from dependency_injector.wiring import Provide, inject

from ProfilerKubeRC.ServiceInit import ServiceInit
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.ServiceInit import ServiceInit
from ProfilerKubeRC.container import TasksContainer
from ProfilerKubeRC.TasksManager import TasksManager
from ProfilerKubeRC.healthcheck import HealthCheck

logger: SLogger = Provide[LoggerContainer.logger_svc]


@inject
def startReplicationController(tasks_manager: TasksManager = Provide[TasksContainer.tasks_manager]):
    crd_config = os.environ.get('CRD_NAME', 'profiler-deployment')
    crd_namespace = os.environ.get('CRD_NAMESPACE', 'default')
    service_init = ServiceInit(crd_config, crd_namespace)
    service_init.runInit()
    HealthCheck.init(service_init)
    tasks_manager.runTasks()


if __name__ == '__main__':
    startReplicationController()