from dependency_injector import containers, providers
from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.KubeClient import KubeLocalClient, KubeEKSClient, KubeInclusterClient
from ProfilerKubeRC.TasksManager import TasksManager

class EngineContainer(containers.DeclarativeContainer):
    """
    Container for kubernetes engine objects
    Supports:
    client for access to local cluster f.e. minicube
    client for access to kubernetes cluster to run from kubernetes inside
    client for access to EKS cluster with aws role permissions
    engine to wrap kubernetes API calls
    """

    config = providers.Configuration()

    # Create client for access to local cluster f.e. minicube
    local_kube_client = providers.Singleton(
        KubeLocalClient
    )

    # Create client for access to kubernetes cluster to run from kubernetes inside
    incluster_kube_client = providers.Singleton(
        KubeInclusterClient
    )

    # Create client for access to EKS cluster with aws role permissions
    eks_kube_client = providers.Singleton(
        KubeEKSClient,
        config.cluster
    )

    # Select active kubernetes client
    kube_client = providers.Selector(
        config.cluster_type,
        local=local_kube_client,
        eks=eks_kube_client,
        incluster=incluster_kube_client
    )

    # Create class to run kubernetes API
    kube_engine = providers.Singleton(
        KubeEngine,
        kube_client
    )



class TasksContainer(containers.DeclarativeContainer):
    """
    Container to manage multitasking
    """

    tasks_manager = providers.Singleton(TasksManager)


