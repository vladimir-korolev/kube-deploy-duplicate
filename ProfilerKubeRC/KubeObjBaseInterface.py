from abc import ABC, abstractmethod

# Base abstract class to manage Kube deployments
# Public methods:
# - eventHandler: This method should be called from listener as callback
# - update: do steps to change object configuration

class KubeObjBaseInterface(ABC):
        pass