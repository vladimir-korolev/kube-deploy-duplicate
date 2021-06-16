# from __future__ import annotations
from abc import ABC, abstractmethod
import kubernetes.client
from dependency_injector.wiring import inject, Provide

from ProfilerKubeRC.KubeEKSClusterInfo import KubeEKSClusterInfo
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger


class KubeClientConfig:
    """
    Manages kubernetes client configuration.
    Fills some static default values within initialization.

    :param endpoint: (optional) endpoint for the kubernetes cluster API. Can be set later.

    Public methods:
        - getConfiguration(): returns configuration object for client
        - setClusterEndpoint(): update cluster endpoint for API
        - setSessionToken(): update client session token

    """
    def __init__(self, endpoint=None, authorization_type=None):
        self._configuration = kubernetes.client.Configuration()
        self._configuration.verify_ssl = False
        if authorization_type is not None:
            self._configuration.api_key_prefix['authorization'] = authorization_type
        self._configuration.host = endpoint

    def getConfiguration(self):
        return self._configuration

    def setSessionToken(self, token):
        if token is not None:
            self._configuration.api_key['authorization'] = token
        return self._configuration


class KubeClient:
    """
    Manage kubernetes client. Abstract class

    Public methods:
    - getApiClient(): returns kubernetes.client.ApiClient for executing  API request
    """

    def __init__(self):
        self._setLogger()

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    @abstractmethod
    def getApiClient(self) -> kubernetes.client.ApiClient:
        pass


class KubeLocalClient(KubeClient):
    """
    Kubernetes client to work with a local cluster, f.e. minikube
    Public methods:
    - getApiClient(): returns kubernetes.client.ApiClient for executing  API request
    """

    def __init__(self):
        super().__init__()
        self._logger.debug("Initializing local cluster")
        kubernetes.config.load_kube_config()

    def getApiClient(self) -> kubernetes.client.ApiClient:
        return None

class KubeInclusterClient(KubeClient):
    """
    Kubernetes client to run inside kubernetes pod
    Public methods:
    - getApiClient(): returns kubernetes.client.ApiClient for executing  API request
    """

    def __init__(self):
        super().__init__()
        self._logger.debug("Initializing local cluster")
        kubernetes.config.load_incluster_config()

    def getApiClient(self) -> kubernetes.client.ApiClient:
        return None


class KubeEKSClient(KubeClient):
    """
    Kubernetes client to work with EKS under an assumed role
    Public methods:
    - getApiClient(): returns kubernetes.client.ApiClient for executing  API request
    """

    def __init__(self, cluster_name, region_name='us-east-1', lag=60):
        super().__init__()
        self._logger.debug("Initializing EKS cluster")
        self._cluster = KubeEKSClusterInfo(cluster_name, region_name, lag)
        self._logger.debug(self._cluster)
        self._refreshSessionToken()

    def getApiClient(self) -> kubernetes.client.ApiClient:
        if self._cluster.isTokenExpired():
            self._refreshSessionToken()
        return self._api_client

    def _refreshSessionToken(self):
        config = KubeClientConfig(self._cluster.getEndpoint(), self._getAuthorizationType())
        self._api_client = kubernetes.client.ApiClient(config.setSessionToken(self._cluster.getSessionToken()))

    def _getAuthorizationType(self) -> str:
        return 'Bearer'
    

class AKubeClientFabric(ABC):
    """
    Abstract class to get client
    """

    @staticmethod
    @abstractmethod
    def getKubeLocalClient(self, hostname) -> KubeClient:
        pass

    @staticmethod
    @abstractmethod
    def getKubeEKSClient(self, cluster_name, region_name='us-east-1', lag=60) -> KubeClient:
        pass


class KubeClientFabric(AKubeClientFabric):

    @staticmethod
    def getKubeLocalClient() -> KubeClient:
        return KubeLocalClient()

    @staticmethod
    def getKubeEKSClient(cluster_name, region_name='us-east-1', lag=60) -> KubeClient:
        return KubeEKSClient(cluster_name, region_name, lag)



