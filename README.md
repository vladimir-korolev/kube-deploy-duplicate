






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


  