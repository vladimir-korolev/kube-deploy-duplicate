from math import ceil
import time

from kubernetes import client, config
from kubernetes.client import V1ConfigMap, V1ObjectMeta, V1Deployment
from ProfilerKubeRC.KubeDeploymentTemplates import KubeDeploymentTemplates

profiler_test_config = {
    'profiler_deployment': 'profiler-worker-profiler',
    'source_deployment': 'profiler-worker',
    'scale_factor': 0.5,
    'cloned_image': 'bitnami/apache',
    'env': {'name': 'PROFILER_ENABLED', 'value': 'True'},
    'namespace': None,
    'testclient': None
}

def clear_profiler_test_config():
    profiler_test_config['profiler_deployment'] = 'profiler-worker-profiler'
    profiler_test_config['source_deployment'] = 'profiler-worker'
    profiler_test_config['scale_factor'] = 0.5
    profiler_test_config['cloned_image'] = None
    profiler_test_config['env'] = None
    profiler_test_config['namespace'] = None
    profiler_test_config['testclient'] = None


def run_worker(kube):
    deployments = kube.get_deployments()
    worker_deploy = deployments.get('profiler-worker')
    assert worker_deploy is not None

    pods = worker_deploy.get_pods()
    assert len(pods) == 2, 'worker should deploy with two replicas'

    return worker_deploy

def assert_source_profilers(testName, replicas):
    profiler_deploy = None
    for i in range(5):
        deployments = profiler_test_config['testclient'].get_deployments()
        profiler_deploy = deployments.get(profiler_test_config['source_deployment'])
        if profiler_deploy is not None:
            break
        time.sleep(10)

    assert profiler_deploy is not None

    running_replicas = int(profiler_deploy.__dict__.get('obj').status.replicas)
    print("running replicas=" + str(running_replicas))

    assert running_replicas == replicas if replicas > 0 else 0, 'worker should deploy with %s replicas' % (replicas)

    print("Test % success" % testName)

def getEnvValue(deployment, env_name):
    env_list = deployment.spec.template.spec.containers[0].env
    if env_list is not None:
        for item in env_list:
            if item.name == env_name:
                return item.value
    return None

def assertEnv(deployment, env):
    if env is not None:
        assert env.get('value', None) == getEnvValue(deployment, env.get('name', None)), "ENV variable %s: %s must be set in cloned deployment" % (
                profiler_test_config['env'].get('name', '---'), profiler_test_config['env'].get('value', '---'))
        print("Assert environment variables check SUCCESS")

def assertImage(source_deployment, profiler_deployment):
    if profiler_test_config.get('cloned_image', None) is not None:
        image = profiler_test_config.get('cloned_image')
    else:
        image = source_deployment.spec.template.spec.containers[0].image
    assert image == profiler_deployment.spec.template.spec.containers[0].image,  "Cloned image is %s, but have to be %s" % (profiler_deployment.spec.template.spec.containers[0].image, image)
    print("Assert cloned image check SUCCESS")

def assertDeploy(source_deployment, profiler_deployment):
    assertEnv(profiler_deployment, profiler_test_config.get('env', None))
    assertImage(source_deployment, profiler_deployment)

def readDeployment(name) -> V1Deployment:
    config.load_kube_config()
    api = client.AppsV1Api()
    return api.read_namespaced_deployment(name=name, namespace=profiler_test_config['namespace'])

def updateReplicas(test_name, replicas):
    config.load_kube_config()
    patch_body = KubeDeploymentTemplates.buildScalePatch(replicas)
    api = client.AppsV1Api()
    api.patch_namespaced_deployment(name=profiler_test_config['source_deployment'], namespace=profiler_test_config['namespace'], body=patch_body)
    print("Deployment %s set replicas=%s" % (profiler_test_config['source_deployment'], replicas))
    time.sleep(5)
    source_deployment = readDeployment(profiler_test_config['source_deployment'])
    deployment = readDeployment(profiler_test_config['profiler_deployment'])
    assert deployment.spec.replicas == ceil(profiler_test_config['scale_factor'] * replicas), 'cloned worker should deploy with %s replicas, but it deployed with %s replicas' % (ceil(profiler_test_config['scale_factor'] * replicas), deployment.spec.replicas)
    print("Test %s is success" % test_name)
    assertDeploy(source_deployment, deployment)

def assertUpdateDeployment(env_update):
    config.load_kube_config()
    source_deployment = readDeployment(profiler_test_config['source_deployment'])
    container_name = source_deployment.spec.template.spec.containers[0].name
    env_update_var = env_update.split(':')
    patch_body = KubeDeploymentTemplates.buildEnvPatch(container_name, env_update_var)
    api = client.AppsV1Api()
    api.patch_namespaced_deployment(name=profiler_test_config['source_deployment'], namespace=profiler_test_config['namespace'], body=patch_body)
    while getEnvValue(readDeployment(profiler_test_config['source_deployment']), env_update_var[0]) != env_update_var[1]:
        print("Waiting for updating env variable in source")
        time.sleep(5)
    i = 0
    while i < 10 and getEnvValue(readDeployment(profiler_test_config['profiler_deployment']), env_update_var[0]) != env_update_var[1]:
        print("Waiting for updating env variable in cloned %s != %s" %(getEnvValue(readDeployment(profiler_test_config['profiler_deployment']), env_update_var[0]), env_update_var[1]))
        time.sleep(5)
        i += 1
    source_deployment = readDeployment(profiler_test_config['source_deployment'])
    deployment = readDeployment(profiler_test_config['profiler_deployment'])
    assertDeploy(source_deployment, deployment)