#!/bin/sh
docker build -t $1/grove-profiler:minikube .
docker push $1/grove-profiler:minikube
kubectl create namespace profiler-m
kubectl -n profiler-m apply -f minikube/profiler-worker.yaml
sed "s/DOCKERREGISTRY/$1/g" minikube/values.orig.yaml > minikube/values.yaml
helm -n profiler-m upgrade --install ddprofiler charts/ddprofiler-rc -f minikube/values.yaml

