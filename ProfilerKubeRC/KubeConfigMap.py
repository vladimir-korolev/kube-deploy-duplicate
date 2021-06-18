import yaml
from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide
from ProfilerKubeRC import KubeEngine
from ProfilerKubeRC.KubeDeployment import DeploymentConfigDto
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.logger import LoggerContainer, SLogger
from ProfilerKubeRC.KubeEventListener import KubeEventHandlerInterface

class KubeConfigMap(KubeEventHandlerInterface):
    """
    Handles configmap objects. At present this class uses to parse configuration from configmap object
    :param name: name of deployment
    :param namespace: working kubernetes namespace
    :param type: type of configmap data

    Public methods:
        - update: Not used yet. In future it have to generate deployment event

    Private methods:

    """
    def __init__(self, name, namespace, type='yaml'):
        self._setLogger()
        self._setKubeEngine()
        self._name = name
        self._namespace = namespace
        self._type = type
        self._data = ''
        self.refresh()

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    @inject
    def _setKubeEngine(self, engine: KubeEngine = Provide[EngineContainer.kube_engine]):
        self._kube_engine = engine

    def refresh(self):
        self._data = self._kube_engine.readConfigMap(self._name, self._namespace)

    def getContent(self):
        return self._data

    def getName(self):
        return self._name

    def getNamespace(self):
        return self._namespace

    def update(self, event):
        pass

    def getConfigurationData(self):
        return self._data.data

    def getConfigurationValue(self, variable, config_data=None):
        if config_data is None:
            config_data = self._data
        try:
            value = config_data.data[variable]
            if value is None:
                self._logger.warning("Variable %s is not found in the configmap" % variable)
                return None
            if self._type == 'yaml':
                return yaml.safe_load(value)
        except Exception as e:
            self._logger.exception(e)
            return None

    def eventHandler(self, event):
        try:
            self._logger.debug("Running configmap event handler")
            if event['type'] == 'MODIFIED' and event['object'].metadata.name == self._name:
                self.update()
        except Exception as e:
            print(e)

    def diffConfig(self, old_config, key) -> [DeploymentConfigDto]:
        old_config_data = self.getConfigurationValue(key, old_config)
        current_config_data = self.getConfigurationValue(key)
        change_list = []
        for ns, ns_config in current_config_data.items():
            if old_config_data.get(ns, None) is not None:
                for deployment_name, deployment_value in ns_config.get('deployments', {}).items():
                    if old_config_data[ns].get('deployments', None) is not None and old_config_data[ns]['deployments'].get(deployment_name, None) is not None:
                        if deployment_value != old_config_data[ns]['deployments'].get(deployment_name):
                            self._logger.info(
                                "Configuration for %s in %s namespace has been changed" % (deployment_name, ns))
                            change_list.append(DeploymentConfigDto(deployment_name, deployment_value))
                        else:
                            self._logger.debug(
                                "Configuration for %s in %s namespace has not been changed" % (deployment_name, ns))
                    else:
                        self._logger.error(
                            "Deploy %s is not found in configuration. Deploy can't be removed from configiration" % deployment_name)
            else:
                self._logger.error(
                    "Namespace %s is not found in configuration. Namespace can't be modified in configiration" % ns)
        return change_list

    def getConfigData(self, key):
        current_config_data = self.getConfigurationValue(key)
        config_data = []
        for ns, ns_config in current_config_data.items():
            for deployment_name, deployment_value in ns_config.get('deployments', {}).items():
                config_data.append(DeploymentConfigDto(deployment_name, deployment_value))
        return config_data


