import concurrent.futures
import time
from dependency_injector.wiring import inject, Provide
from ProfilerKubeRC.KubeConfigMap import KubeConfigMap
from ProfilerKubeRC.KubeDeployment import AKubeDeployment, KubeDeploymentWithClone, DeploymentConfigDto
from ProfilerKubeRC.KubeEventListener import KubeDeploymentEventListener, KubeCmEventListener
from ProfilerKubeRC.KubeEventListener import KubeEventListenerInterface, KubeEventHandlerInterface
from ProfilerKubeRC.KubeCrd import KubeCrd
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.TasksManager import TasksManager
from ProfilerKubeRC.container import TasksContainer
# from ProfilerKubeRC.healthcheck import HealthCheck


class ServiceInit:
    configuraton_tag = 'config'

    def __init__(self, crd_name, crd_namespace):
        self._setLogger()
        self._setTasksManager()
        crdConfig = KubeCrd(crd_name, crd_namespace)
        config = None
        while config is None:
            self._logger.info("Waiting for crd %s in namespace %s" % (crd_name, crd_namespace))
            time.sleep(1)
            config = crdConfig.getInitConfigCrd()
        ServiceInit.configuraton_tag = config["cmConfigTag"]
        self._configmap = KubeConfigMap(config["cmName"], config["cmNamespace"])
        self._logger.debug("Start service initialization")
        self._config = self._configmap.getConfigurationValue(ServiceInit.configuraton_tag)
        if self._config is None:
            self._logger.error("No config found in the configmap")
            return
        else:
            self._logger.debug("Configmap is loaded")
        self._kube_event_listeners = []
        self._kube_cm_listener: KubeEventListenerInterface = None
        self._kube_deployments: [AKubeDeployment] = []

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    @inject
    def _setTasksManager(self, tasks_manager: TasksManager = Provide[TasksContainer.tasks_manager]):
        self._tasks_manager = tasks_manager


    def runInit(self):
        for ns, ns_config in self._config.items():
            kube_event_listener = KubeDeploymentEventListener(ns)
            for deployment_name, deployment_value in ns_config.get('deployments', {}).items():
                try:
                    kube_deployment = KubeDeploymentWithClone(
                        name=deployment_name,
                        namespace=ns,
                        name_suffix=deployment_value.get('name_suffix', '0'),
                        cloned_factor=deployment_value.get('scale_factor', '0'),
                        image=deployment_value.get('cloned_image', None),
                        env=deployment_value.get('env', None)
                    )
                    self._kube_deployments.append(kube_deployment)
                    kube_event_listener.addEventHandler(kube_deployment)
                    self._logger.info('====================================================================> Deployment %s has been added to handle' % kube_deployment.getName())
                except Exception as e:
                    self._logger.exception(e)
            self._updKubeDeployments(self._configmap.getConfigData(ServiceInit.configuraton_tag))  # resync current running deployments with configmap
            self._kube_event_listeners.append(kube_event_listener)
            self._kube_cm_listener = KubeCmEventListener(self._configmap.getNamespace())
            self._kube_cm_listener.addEventHandler(self)
            self.runListeners()
        self._logger.info("Services have been initialized")

    def runListeners(self):
        for listener in self._kube_event_listeners:
            self._tasks_manager.addTask(listener.runWatcher, ())
        self._tasks_manager.addTask(self._kube_cm_listener.runWatcher, ())


    def _updKubeDeployments(self, change_list: [DeploymentConfigDto]):
        for item in change_list:
            self._logger.info("Config has been changed for deploy %s" % item.name)
            for deployment in self._kube_deployments:
                if deployment.getName() == item.name:
                    deployment.updateClonedDeploymentConfig(item)

    def eventHandler(self, event):
        if event['object'].kind == 'ConfigMap' and event['object'].metadata.name == self._configmap.getName() and event['type'] == 'MODIFIED':
            old_config = self._configmap.getContent()
            self._configmap.refresh()
            self._updKubeDeployments(self._configmap.diffConfig(old_config, ServiceInit.configuraton_tag))

    def healthCheck(self):
        health = True
        for deployment in self._kube_deployments:
            health = health & deployment.healthCheck()
        return health

