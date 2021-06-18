# kubectl -n kubetest-ddprofiler apply -f tests/demo/prereq/
PYTHONPATH=$(pwd) LOGLEVEL='DEBUG' pytest --kube-config ~/.kube/config --kube-context minikube -s tests
