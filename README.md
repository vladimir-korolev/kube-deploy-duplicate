This kubernetes operator creates and maintains clones of the existing kubernetes deployment according to the configuration rules.
It responsible for:
 - number of replicas of the cloned deployment have to comply with rules in the configuration
 - use special image for the cloned deployment
 - add extra environment variables to the cloned deployment  
 
LIMITATION:
  - only one container is supported in source deployment
  - if we remove an env item in a source deployment it won't be removed in cloned one because it used kubernetes patch API call to update the cloned replica 
  - if a source deployment object has deleted, the cloned deployment object will running with replicas=0 
  - when we start the application first time we can have error message from Kubernetes API about the deployment can't be found. Please, don't disturb about it
  
# How to configure

##Start application
To start application run:
python startApp.py CLIENT=<TYPE_OF_K8S_CLUSTER>;CLUSTER=<EKS_CLUSTER_NAME>;CRD_NAME=<CRD_NAME>;CRD_NAMESPACE=<CRD_NAMESPACE>;LOGLEVEL=<LOG_LEVEL>
where:
```
    TYPE_OF_K8S_CLUSTER: Type of kubernetes cluster.
        Now supported values:
        - "local" to work with local k8s cluster like minikube or bare metall
        - "eks" to work with EKS cluster under assigned role.
        - "incluster" to run from inside k8s cluster
    EKS_CLUSTER_NAME: Only for EKS cluster. It's a working context name
    CRD_NAME: Name of a CustomResourseDefinitions object to find configmap object with configuration
    CRD_NAMESPACE: Namespace where the CustomResourseDefinitions object is
    LOGLEVEL: can be INFO, ERROR, WARNING, DEBUG
```
CustomResourseDefinitions object and configmap object must be deployed to the cluster before starting application
    
Examples:
- start application with minikube
```
python startApp.py CLIENT=local;CRD_NAME=ddprof-ddprof-rcconfig;CRD_NAMESPACE=profiler-m;LOGLEVEL=DEBUG
```

- start application with eks
```
python startApp.py CLIENT=eks;CLUSTER=staging_app1;CRD_NAME=ddprof-ddprof-rcconfig;CRD_NAMESPACE=profiler-m;LOGLEVEL=INFO
```

- start application in kubernetes pod inside cluster. It is a production mode
```
python startApp.py CLIENT=incluster;CRD_NAME=ddprof-ddprof-rcconfig;CRD_NAMESPACE=profiler-m;LOGLEVEL=INFO
```
Application can be deployed in separate namespace from managed deployment and we don't need provide some extra permissions to production namespace for user who should start this application  

##Configuration objects
Configuration rule are in profiler-rc-config variable in a k8s configmap object. Schema of the configmap:
```
   <CONFIGURATION_TAG>:                         # This tag which configured in CustomResourseDefinitions objec
    <namespace>:                                # Namespace where we have to run the clone
       deployments:                             # Type k8s object for cloning. Supported only "deployment" 
        <name of deployment>:                   # Mandatory. Name of source deployment    
          env: "<name>: <value>"                # Optional. Extra environment variable to add to the clone
          scale_factor: <float value>           # Mandatory. Factor to calculate number of replics of the clone
          name_suffix: <value>                  # Mandatory. Suffix to add to name of the clone
          image: <value>                        # Optional. Separate image for the cloned deployment if it is necessary
        <name of next deployment>:
        .
        .
        .
```
Example:
```
  profiler-rc-config: |-
    default:
      deployments:
        nginx-deployment:
          env: "PROFILING_ENABLED: True"
          scale_factor: "0.5"
          name_suffix: "profiler"
        nginx-deployment-2:
          env: "PROFILING_ENABLED: True"
          image: "busybox"
          scale_factor: "0.1"
          name_suffix: "profiler"
```

Rules to search a configmap with configuration are provided in k8s CustomResourseDefinitions object (it's not very useful at present but we have a possibility to use multiple configmaps with configuration in future):
List of fields of the CustomResourseDefinitions object:

        "cmConfigTag": <CONFIGURATION_TAG>                        # It is name of variable in configmap where cloned deployment rules are
        "cmName": "ddprof-rcconfig",                              # Name of a configmap with configuration
        "cmNamespace": profiler_test_config['namespace'],         # Namespace where the configmap is
        "ruleType": "configmap"                                   # It means the rules are in aconfigmap

Example:

        "apiVersion": "crds.grove/v1",
        "kind": "DDProfCrd",
        "metadata": {"name": "ddprof-ddprof-rcconfig"},
        "cmConfigTag": "profiler-rc-config",
        "cmName": "ddprof-rcconfig",
        "cmNamespace": profiler_test_config['namespace'],
        "ruleType": "configmap"

## Run application in kubernetes cluster
To run application in kubernetes cluster we have to install helm chart:
- add grove-harbor repository
        helm repo add --username=<> --password=<> grove-harbor https://harbor.tools.grove.co/chartrepo/library
- modify values.yaml. You can look at comments in charts/ddprofiler-rc/values.yaml
- install ddprofiler-rc chart from grove-harbor repository -f values.yaml
        helm update --install grove-harbor ddprofiler-rc:0.0.3 
This chart includes:
     - CustomResourseDefinitions object
     - Configmap object
     - Deployment object
     - RBAC configuration

Example of values.yaml in charts/ddprofiler-rc/ddprofiler-rc-config.example.yaml

## Run tests with minikube
Run from project root directory:
PYTHONPATH=$(pwd) LOGLEVEL='ERROR' pytest --kube-config ~/.kube/config --kube-context minikube -s tests

Look at a short manual: tests/readme.md
     
       
# How it works
This application starts in separate threads:
- event listener to watch k8s deployments' changes
- event listener to watch k8s configmaps' changes
- web service to process healthchecks 

The deployments event listeners are watching k8s deployments events(like "kubectl get deployments -w"). For each event it have to be run an event handler. The event handler filters events and handles them. 
The event handler can update a cloned deployment only not a source deployment. Event handler gets source deploy, creates the same copy, applies rules in configuration and creates a new deploy or patches the existing one. Any changes in source deployment will start update a cloned deployment.
Because of the cloned deploy is being patched, only changes apply to it without restarting a cloned object if it isn't necessary

The configmap event listener are watching k8s configmaps events(like "kubectl get configmaps -w"). For each event it have to be run an event handler. The event handler filters events and handles them.
The event handler creates a config DTO object and run an update config method in the deployments (TODO: generate an event instead of direct call update deployment method)

The web service just checks is the application works and returns HTTP 200 is OK. It just checks required number replicas of the cloned deployment


Sequence diagram


    Service init     KubeConfigMap     KubeDeployment     KubeEventListener   Configmap Events  Deploymet Events 
         |                 |                 |                   |                 |                   |  
         |---------------->|                 |                   |                 |                   |
         |ReadingConfig    |                 |                   |                 |                   |
         |<----------------|                 |                   |                 |                   |
         |                 |                 |                   |                 |                   |
         | Registering deployment listener                       |                 |                   |
         |-----------------------------------------------------> |                 |                   |
         | Registering configmap listener                        |                 |                   |
         |-----------------------------------------------------> |                 |                   |
         |                 |                 |                   | Configmap event |                   |      
         |                 Run event handler                     | <---------------|                   |
         |<----------------------------------------------------- |                 |                   |
         | --------------------------------->|                   |                 |                   |
         |              Patch deployments    |                   |            Deployment event         |
         |                 |                 | Run event handler |<----------------------------------- |   
         |                 |                 |<----------------- |                 |                   |        
         |                 |                 | Patch deployments |                 |                   |


  