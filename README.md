
LIMITATION:
  only one container is supported in source deployment
  if we remove an env item in a source deployment it won't be removed in cloned one because it used kubernetes patch API call to update the cloned replica 


Event listener watches events. For each event runs event handler. Event handler checks is its event by object name in deployment and handle it. 
Event hahdler updates a cloned deployment
Update checks is there any changes by resource version field and run build a new cloned deployment from source procedure and then patch k8s object
Because of using patch k8s object updates only changes without restarting a cloned object if it isn't necessary  




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


  