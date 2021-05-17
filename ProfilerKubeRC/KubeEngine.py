import kubernetes
from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide
from kubernetes.client.rest import ApiException
from kubernetes import watch
from contextlib import suppress

from ProfilerKubeRC.KubeClient import KubeClient
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger


def kubapi_call(func):
    def wrapper(*args, **kwargs):
        try:
            KubeEngine.logger.debug("K8s API call: %s" % func)
            return func(*args, **kwargs)
        except ApiException as e:
            KubeEngine.logger.error("Exception when calling %s: %s\n" % (func, e))
            return None
        except Exception as e:
            KubeEngine.logger.exception(e)
            return None
    return wrapper

class AKubeEngine(ABC):

    @abstractmethod
    def readDeployment(self, name, namespace):
        pass

    @abstractmethod
    def createDeployment(self, deployment, namespace):
        pass

    @abstractmethod
    def readConfigMap(self, name, namespace):
        pass

    @abstractmethod
    def watchDeployments(self, namespace, callback=None):
        pass

    @abstractmethod
    def watchConfigMaps(self, namespace, callback=None):
        pass

    @abstractmethod
    def patchDeployment(self, name, namespace, patch_body):
        pass

class KubeEngine(AKubeEngine):
    logger: SLogger = None

    def __init__(self, api_client):
        KubeEngine.setLogger()
        KubeEngine.logger.debug("Starting k8s engine")
        self._api_client = api_client
        self._api_appsv1 = kubernetes.client.AppsV1Api(self._getApiClient().getApiClient())         # It cant't use just api_client variable
        self._api_corev1 = kubernetes.client.CoreV1Api(self._getApiClient().getApiClient())         # It cant't use just api_client variable

    @inject
    def setLogger(logger_svc: SLogger = Provide[LoggerContainer.logger_svc]):
        KubeEngine.logger = logger_svc

    def getLogger(self):
        return KubeEngine.logger

    def _getApiClient(self) -> KubeClient:
        return self._api_client

    @kubapi_call
    def createDeployment(self, deployment, namespace):
        KubeEngine.logger.debug("Creating deployment %s in %s" % (deployment.metadata.name, namespace))
        return self._api_appsv1.create_namespaced_deployment(namespace, deployment)

    @kubapi_call
    def readDeployment(self, name, namespace):
        KubeEngine.logger.debug("Reading deployment %s in %s" % (name, namespace))
        return self._api_appsv1.read_namespaced_deployment(name, namespace, pretty=False)

    @kubapi_call
    def readConfigMap(self, name, namespace):
        return self._api_corev1.read_namespaced_config_map(name=name, namespace=namespace)

    def watchDeployments(self, namespace, callback=None):
        KubeEngine.logger.debug("Deployments watcher has been started")
        while True:
            w = watch.Watch()
            try:
                for event in w.stream(self._api_appsv1.list_namespaced_deployment, namespace=namespace):
                    # KubeEngine.logger.debug("Event: %s %s %s %s %s %s %s %s" % (event['type'], event['object'].metadata.name,
                    #         event['object'].status.updated_replicas, event['object'].status.conditions[0].status,
                    #         event['object'].status.conditions[1].status, event['object'].status.conditions[0].type,
                    #         event['object'].status.conditions[1].type, event['object'].metadata.resource_version))
                    if callback is not None and event['object'].status.conditions[0].status and event['object'].status.conditions[1].status:
                        KubeEngine.logger.info("Event: %s %s" % (event['type'], event['object'].metadata.name))
                        callback(event)
            except ApiException as e:
                KubeEngine.logger.error("Exception when calling AppsV1Api->list_namespaced_deployment: %s\n" % e)
            except Exception as ex:
                KubeEngine.logger.exception(ex)

    def watchConfigMaps(self, namespace, callback=None):
        KubeEngine.logger.debug("Configmaps watcher has been started")
        while True:
            w = watch.Watch()
            try:
                for event in w.stream(self._api_corev1.list_namespaced_config_map, namespace=namespace):
                        KubeEngine.logger.info("Event: %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].metadata.resource_version))
                        if callback is not None:
                            callback(event)
            except ApiException as e:
                KubeEngine.logger.error("Exception when calling CoreV1Api->list_namespaced_configmap: %s\n" % e)
            except Exception as ex:
                KubeEngine.logger.exception(ex)

    @kubapi_call
    def patchDeployment(self, name, namespace, patch_body):
        return self._api_appsv1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch_body)

    @kubapi_call
    def getCrd(self, crd_group, crd_version, namespace, crd_plural, name):
        custom_api = kubernetes.client.CustomObjectsApi(self._getApiClient().getApiClient())
        crd = custom_api.get_namespaced_custom_object(
            crd_group,
            crd_version,
            namespace,
            crd_plural,
            name
        )
        return crd # {x: crd[x] for x in ('ruleType', 'selector', 'namespace')}



