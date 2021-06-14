import pytest

from tests.kube_tests_lib import updateReplicas, profiler_test_config, assertUpdateDeployment, clear_profiler_test_config, assert_source_profilers, run_worker
from tests.mainservice import createCrd, createConfigMap, startReplicationControllerApp, waitProfilerStart, startProfilerManually



def runProfilerTests(test_name):
    print("Start profiler tests")
    waitProfilerStart('profiler_deployment')
    assert_source_profilers("Init run profiler test", 2)
    updateReplicas(test_name + ": scale up replicas", 6)
    updateReplicas(test_name + ": scale up replicas", 0)
    updateReplicas(test_name + ": scale up replicas", 4)
    assertUpdateDeployment("TEST2: testvalue")

@pytest.mark.applymanifests('demo', files=['profiler-worker.yaml'])
def runProfilerTestWithStartSource(test_name):
    print("******************************************************************************************")
    startProfilerManually()
    waitProfilerStart('profiler_deployment')
    runProfilerTests(test_name)

def test_start_profiler_when_no_workers(kube):
    print("Start test_start_profiler_when_no_workers")
    clear_profiler_test_config()
    profiler_test_config['testclient'] = kube
    profiler_test_config['namespace'] = kube.namespace
    createCrd()
    createConfigMap()
    startReplicationControllerApp(runProfilerTestWithStartSource, "\n\n\n****************\nStart profiler before workers have been started\n****************\n")

@pytest.mark.applymanifests('demo', files=['profiler-worker.yaml'])
def test_start_profiler_when_after_workers(kube):
    print("Start test_start_profiler_after_workers")
    clear_profiler_test_config()
    profiler_test_config['testclient'] = kube
    # wait for the manifests loaded by the 'applymanifests' marker
    # to be ready on the cluster
    kube.wait_for_registered(timeout=30)
    worker_deploy = run_worker(kube)                    # Start worker services as sources
    profiler_test_config['namespace'] = kube.namespace
    createCrd()
    createConfigMap()
    startReplicationControllerApp(runProfilerTests, "\n\n\n****************\nStart profiler when workers have already ran\n****************\n")

@pytest.mark.applymanifests('demo', files=['profiler-worker.yaml'])
def test_start_profiler_with_image_modify(kube):
    print("Start test_start_profiler_with_image_modify")
    clear_profiler_test_config()
    profiler_test_config['testclient'] = kube
    profiler_test_config['cloned_image'] = 'bitnami/apache'
    # wait for the manifests loaded by the 'applymanifests' marker
    # to be ready on the cluster
    kube.wait_for_registered(timeout=30)
    worker_deploy = run_worker(kube)                    # Start worker services as sources
    profiler_test_config['namespace'] = kube.namespace
    createCrd()
    createConfigMap()
    startReplicationControllerApp(runProfilerTests, "\n\n\n****************\nStart profiler when workers have already ran\n****************\n")

@pytest.mark.applymanifests('demo', files=['profiler-worker.yaml'])
def test_start_profiler_with_env_modify(kube):
    print("Start test_start_profiler_with_env_modify")
    clear_profiler_test_config()
    profiler_test_config['testclient'] = kube
    profiler_test_config['env'] = {'name': 'PROFILER_ENABLED', 'value': 'True'}
    # wait for the manifests loaded by the 'applymanifests' marker
    # to be ready on the cluster
    kube.wait_for_registered(timeout=30)
    worker_deploy = run_worker(kube)                    # Start worker services as sources
    profiler_test_config['namespace'] = kube.namespace
    createCrd()
    createConfigMap()
    startReplicationControllerApp(runProfilerTests, "\n\n\n****************\nStart profiler when workers have already ran\n****************\n")



