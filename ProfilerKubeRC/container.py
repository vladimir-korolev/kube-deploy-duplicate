import sys
from dependency_injector import containers, providers
from ProfilerKubeRC.KubeClient import KubeLocalClient, KubeEKSClient, KubeInclusterClient
from ProfilerKubeRC.KubeEngine import KubeEngine




class EngineContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    local_kube_client = providers.Singleton(
        KubeLocalClient
    )

    incluster_kube_client = providers.Singleton(
        KubeInclusterClient
    )

    eks_kube_client = providers.Singleton(
        KubeEKSClient,
        config.cluster
    )

    kube_client = providers.Selector(
        config.cluster_type,
        local=local_kube_client,
        eks=eks_kube_client,
        incluster=incluster_kube_client
    )

    kube_engine = providers.Singleton(
        KubeEngine,
        kube_client
    )

    # kube_config = providers.Singleton(
    #     KubeConfigMap,
    #     kube_engine,
    #     config.cm_name,
    #     config.cm_namespace
    # )





# @inject
# def getKubeEngine(engine: KubeEngine = Provide[EngineContainer.kube_engine]):
#     return engine
#
#
# def printClient(client):
#     print(client)
#
# @inject
# def setKubeClient(client: KubeClient = Provide[EngineContainer.kube_client]):
#     print(client)

# @inject
# def setKubeDeploymentWeb(deployment: KubeDeploymentWithClone = Provide[EngineContainer.kube_deployment_web]):
#     return deployment


if __name__ == '__main__':
    engineContainer = EngineContainer()
    engineContainer.config.api_key.from_env('API_KEY')
    engineContainer.config.timeout.from_env('TIMEOUT')
    engineContainer.config.cluster_type.from_env('CLIENT')
    engineContainer.config.cluster.from_env('CLUSTER')
    engineContainer.config.region.from_env('REGION')
    engineContainer.config.region.from_env('CM_NAME')
    engineContainer.config.region.from_env('CM_NAMESPACE')

    # container.config.namespace.from_env('NAMESPACE')
    # container.config.namesuffix.from_env('NAMESUFFIX')
    # container.config.deployments.web.name.from_env('WEB_DEPLOYMENT')
    # container.config.deployments.web.factor.from_env('WEB_CLONE_FACTOR')

    engineContainer.wire(modules=[sys.modules[__name__]])

    # client = setKubeClient()
    # kube_engine = getKubeEngine()

    # deployment = setKubeDeploymentWeb()


    # deployment = KubeDeploymentWithClone(
    #     kube_engine,
    #     container.config.deployments.web.name(),
    #     container.config.namespace(),
    #     container.config.namesuffix(),
    #     container.config.deployments.web.factor())
    #


    # service = container.service()
    # service.printme()

    # print(deployment)



