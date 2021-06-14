These tests are for verifying cloned deployment behavior

#### How to run tests
To run test run the command from the project root directory:
PYTHONPATH=$(pwd) LOGLEVEL='ERROR' pytest --kube-config ~/.kube/config --kube-context minikube -s tests

#### List of tests
The following tests will be ran:
- Start with no source deployment is running
- Start with source deployments are running
- Start with no cloned deployment image configuration
- Start with no cloned deployment environment variable configuration

For each that tests runs checks with conditions:
+ Scale deployment up (to 6) 
  + number of cloned replica should be 3                  
- Scale deployment down (to 3)
  + number of cloned replica should be 2  
- Scale deployment up (to 4)
  + number of cloned replica should be 2
- Update environment variable in source deployment
  + the new environment variable have to be add/updated in cloned deployment
- Update image in source deployment
  + if cloned image is not configured in config map to be updated in cloned deployment otherwise it don't have to be updated

