import sys
import os
import time
import multiprocessing
from kubernetes import client, config
from kubernetes.utils import create_from_yaml
from kubernetes.client import V1ConfigMap, V1ObjectMeta, V1Deployment, V1CustomResourceDefinition, V1ObjectMeta
from kubernetes.client import V1CustomResourceDefinitionSpec, V1CustomResourceDefinitionNames, V1CustomResourceDefinitionVersion
from kubernetes.client import V1CustomResourceValidation, V1JSONSchemaProps
from kubernetes.client.exceptions import ApiException, OpenApiException

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
from ProfilerKubeRC.runApp import startReplicationController
from ProfilerKubeRC.KubeDeploymentTemplates import KubeDeploymentTemplates
from ProfilerKubeRC.TasksManager import TasksManager
from ProfilerKubeRC.healthcheck import HealthCheck

from tests.kube_tests_lib import profiler_test_config

logger: SLogger = Provide[LoggerContainer.logger_svc]

"""
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: ddprofcrds.crds.grove
spec:
  group: crds.grove
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          ruleType:
            type: string
          cmNamespace:
            type: string
          cmName:
            type: string
          cmConfigTag:
            type: string
  scope: Namespaced
  names:
    plural: ddprofcrds
    singular: ddprofcrd
    kind: DDProfCrd
    shortNames:
    - ddprofcrd
"""


def initContainer():
    logger_container = LoggerContainer()
    logger_container.config.loglevel.from_env('LOGLEVEL')
    logger_container.wire(modules=[sys.modules[__name__]])
    # logger_container.wire(packages=[ProfilerKubeRC])
    #
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


def createCrd():
    config.load_kube_config()
    try:
        create_from_yaml(k8s_client=None, namespace=profiler_test_config['namespace'], yaml_file='tests/demo/crd.yaml')
    except Exception:
        print("Can't create CRD. May be it has already been installed?")
        pass
    time.sleep(10)
    api = client.CustomObjectsApi()
    ddprofcrd = {
        "apiVersion": "crds.grove/v1",
        "kind": "DDProfCrd",
        "metadata": {"name": "ddprof-ddprof-rcconfig"},
        "cmConfigTag": "profiler-rc-config",
        "cmName": "ddprof-rcconfig",
        "cmNamespace": profiler_test_config['namespace'],
        "ruleType": "configmap"
    }

    api.create_namespaced_custom_object(
        group="crds.grove",
        version="v1",
        namespace=profiler_test_config['namespace'],
        plural="ddprofcrds",
        body=ddprofcrd,
    )
    print("Resource CRD created")

def startProfilerManually():
    create_from_yaml(k8s_client=None, namespace=profiler_test_config['namespace'], yaml_file='tests/demo/profiler-worker.yaml')

def createConfigMap():
    config.load_kube_config()
    api = client.CoreV1Api()
    configmap = V1ConfigMap()
    data = {
        "profiler-rc-config": "profiler-namespace:\n  deployments:\n    profiler-worker:\n      scale_factor: \"scale_factor_value\"\n      name_suffix: \"profiler\"".replace("profiler-namespace", profiler_test_config['namespace']).replace("scale_factor_value", str(profiler_test_config['scale_factor']))
    }
    if profiler_test_config.get('env', None) is not None:
        data["profiler-rc-config"] += "\n      env: \"%s: %s\"" % (profiler_test_config['env'].get('name', None), profiler_test_config['env'].get('value', None))
    if profiler_test_config.get('cloned_image', None) is not None:
        data["profiler-rc-config"] += "\n      cloned_image: \"%s\"" % profiler_test_config['cloned_image']
    configmap.metadata = V1ObjectMeta()
    configmap.metadata.name = "ddprof-rcconfig"
    configmap.data = data
    api.create_namespaced_config_map(namespace=profiler_test_config['namespace'], body=configmap)
    print("Resource ConfigMap created")

def waitProfilerStart(deployment_type):
    config.load_kube_config()
    api = client.AppsV1Api()
    profiler_deployment_obj = None
    while profiler_deployment_obj is None:
        try:
            profiler_deployment_obj = api.read_namespaced_deployment(name=profiler_test_config[deployment_type], namespace=profiler_test_config['namespace'])
        except:
            print("Waiting for profiler deployment has been loaded")
            time.sleep(10)
            pass

def startReplicationControllerApp(testScript, test_name):
    os.environ["CRD_NAMESPACE"] = profiler_test_config['namespace']
    os.environ["CRD_NAME"] = "ddprof-ddprof-rcconfig"
    os.environ["CLIENT"] = "local"
    # os.system('CRD_NAMESPACE="kubetest-ddprofiler" CRD_NAME="ddprof-ddprof-rcconfig" ')
    initContainer()
    p = multiprocessing.Process(target=startReplicationController)
    try:
        p.start()
        testScript(test_name)
    finally:
        p.terminate()


