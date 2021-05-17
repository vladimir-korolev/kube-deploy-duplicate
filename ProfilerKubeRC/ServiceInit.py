import concurrent.futures
from ProfilerKubeRC.KubeConfigMap import KubeConfigMap
from ProfilerKubeRC.KubeDeployment import AKubeDeployment, KubeDeploymentWithClone, DeploymentConfigDto
from ProfilerKubeRC.KubeEventListener import KubeDeploymentEventListener, KubeCmEventListener
from ProfilerKubeRC.KubeEventListener import KubeEventListenerInterface, KubeEventHandlerInterface
from ProfilerKubeRC.KubeCrd import KubeCrd
from ProfilerKubeRC.logger import LoggerContainer
from dependency_injector.wiring import inject, Provide
from ProfilerKubeRC.logger import SLogger


class ServiceInit(KubeEventHandlerInterface):
    configuraton_tag = 'config'

    def __init__(self, crd_name, crd_namespace):
        self._setLogger()
        crdConfig = KubeCrd(crd_name, crd_namespace)
        config = crdConfig.getInitConfigCrd()
        if config is None:
            self._logger.error("No crd %s found in namespace %s" % (crd_name, crd_namespace))
            return
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
                        image=deployment_value.get('image', None)
                    )
                    self._kube_deployments.append(kube_deployment)
                    kube_event_listener.addEventHandler(kube_deployment)
                except Exception as e:
                    self._logger.exception(e)
            self._updKubeDeployments(self._configmap.getConfigData(ServiceInit.configuraton_tag))  # resync current running deployments with configmap
            self._kube_event_listeners.append(kube_event_listener)
            self._kube_cm_listener = KubeCmEventListener(self._configmap.getNamespace())
            self._kube_cm_listener.addEventHandler(self)
        self._logger.info("Services have been initialized")

    def runListeners(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for listener in self._kube_event_listeners:
                executor.submit(listener.runWatcher)
            executor.submit(self._kube_cm_listener.runWatcher)
        self._logger.info("Listeners have been initialized")

    def _updKubeDeployments(self, change_list: [DeploymentConfigDto]):
        for item in change_list:
            self._logger.info("Config has been changed for deploy %s" % item.name)
            for deployment in self._kube_deployments:
                if deployment.getName() == item.name:
                    deployment.updateDeploymentConfig(item)

    def eventHandler(self, event):
        if event['object'].kind == 'ConfigMap' and event['object'].metadata.name == self._configmap.getName() and event['type'] == 'MODIFIED':
            old_config = self._configmap.getContent()
            self._configmap.refresh()
            self._updKubeDeployments(self._configmap.diffConfig(old_config, ServiceInit.configuraton_tag))


