#
# This file contents of:
# - KubeDeployment                  : Base class to work with a deployment object
# - KubeDeploymentReplicasMixin     : Class with methods for working with replicas
# - KubeDeploymentMetadataMixin     : Class with methods for working with metadata
# - KubeDeploymentManager           : Class with methods for reading, writing and managing object
# - KubeDeploymentWithClone         : Class with its clone
# - AKubeDeployment                 : Set of public interfaces with abstract methods to work with a deploy object
# - DeploymentConfigDto             : Object with configuring properties for the deployment
# - KubeDeploymentTemplates         : Set templates to patching deployment object

from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide
from math import ceil
from kubernetes.client import V1Deployment

from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.KubeEventListener import KubeEventHandlerInterface
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger
from ProfilerKubeRC.KubeDeploymentTemplates import KubeDeploymentTemplates


class DeploymentConfigDto:
    """
    DTO object to exchange information about configuration of clone of the deployment object.
    Is filling some static default values within initialization.

    :param name: String: name of deployment
    :param body: Dict: configuration paremeters for deployment

    Public methods:
        - getConfiguration(): returns configuration object for client
        - setClusterEndpoint(): update cluster endpoint for API
        - setSessionToken(): update client session token

    """
    def __init__(self, name, body):
        self.name = name
        self.body = body


class AKubeDeployment(ABC):
    """
    Base abstract class to wrap Kubernetes deployment object.
    To use KubeDeployment methods as abstract interfaces

    Public methods:
        - getName: This method returns name of this wrapper object
        - readDeployment: This method reading deployment object into this class
        - getDeployment: This method returns wrapped deployment object as kubernetes.client.V1Deployment
        - setDeployment(new_deployment): Set wrapped deployment object with new_deployment
    """

    @abstractmethod
    def getName(self) -> str:
        pass

    @abstractmethod
    def readDeployment(self) -> V1Deployment:
        pass

    @abstractmethod
    def getDeployment(self):
        pass

    @abstractmethod
    def setDeployment(self, deployment: V1Deployment):
        pass


class KubeDeployment(AKubeDeployment):
    """
    Base class to wrap Kubernetes deployment object.
    Base method to work with deployment object

    :param name: String: name of deployment
    :param namespace: String: namespace to search/create the deployment
    :param image: String: (optional) image if we have to replace original image with it in this deploymentt

    Public methods:
        - getName: This method returns name of this wrapper object
        - readDeployment: This method reading deployment object into this class
        - getDeploymentName: This method returns name of wrapped deployment
        - setDeploymentName: This method changes name of wrapped deployment
        - getDeployment: This method returns wrapped deployment object as kubernetes.client.V1Deployment
        - setDeployment(new_deployment): Set wrapped deployment object with new_deployment
    """

    def __init__(self, name, namespace, image=None):
        self._name = name                           # Name of deployment. self._deployment can be None if replicas == 0. That's a reason why I duplicated name, namespace and images with _deployment: V1Deployment
        self._image = image                         # Image if we have to replace original image with it in this deployment
        self._namespace = namespace                 # Namespace to search the deployment
        self._deployment: V1Deployment = None       # Wrapped deployment object
        self._setLogger()
        self._setKubeEngine()

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    # Inject kubernetes engine methods
    @inject
    def _setKubeEngine(self, engine: KubeEngine = Provide[EngineContainer.kube_engine]):
        self._kube_engine = engine

    def getName(self) -> str:
        return self._name

    # Reads running deployment from kubernetes
    def readDeployment(self) -> V1Deployment:
        return self._getKubeEngine().readDeployment(self.getName(), self._getNameSpace())

    def getDeployment(self):
        return self._deployment

    # set wrapped deployment object
    def setDeployment(self, deployment: V1Deployment):
        self._name = deployment.metadata.name
        self._deployment: V1Deployment = deployment
        self._namespace = deployment.metadata.namespace

    # Returns an active kuberntes client object
    def _getKubeEngine(self):
        return self._kube_engine

    # returns wrapped kubernetes deployment object: kubernetes.V1Deployment
    # to work with a raw kubernetes object
    def _getDeployment(self) -> V1Deployment:
        return self._deployment

    # sets wrapped kubernetes deployment object: kubernetes.V1Deployment
    def _setDeployment(self, deployment: V1Deployment):
        self._deployment: V1Deployment = deployment
        return self

    # To change the deployment name and wrapped kubernetes ob
    def _setWrappedDeploymentName(self, name):
        if self._deployment is not None:
            self._deployment.metadata.name = name

    # To change the deployment name and wrapped kubernetes ob
    def _setNameWithSync(self, name):
        self._setName1(name)
        self._setWrappedDeploymentName(name)

    def _getNameSpace(self):
        return self._namespace

    # Set wrapped deployment as actual running deployment from kubernetes
    def _refreshDeploymentInfo(self):
        self._setDeployment(self.readDeployment())


class KubeDeploymentReplicasMixin(AKubeDeployment):
    """
    Mixin to manage replicas with KubeDeployment class.
    Can't be implemented standalone.
    May not be consistent with running kubernetes object

    Public methods:
        - getReplicasCount: Get replicas count from wrapped deployment object.
        - setReplicasCount: Update replicas count in wrapped deployment object without call Kubernetetes API
    """
    def getReplicasCount(self) -> int:
        return int(
            self.getDeployment().status.replicas) if self.getDeployment() is not None and self.getDeployment().status is not None and self.getDeployment().status.replicas is not None else 0

    def setReplicasCount(self, replicas):
        if self.getDeployment() is not None:
            self.getDeployment().spec.replicas = replicas


class KubeDeploymentMetadataMixin(AKubeDeployment):
    """
    Mixin to manage metadata info with KubeDeployment class.
    Can't be implemented standalone
    May not be consistent with running kubernetes object

    Private methods:
        - _updateMetadataAttr: Update metadata info in the wrapped deployment object to allow to start a new deployment with this metatada
        - _clearStatusInfo: Clear actual running deployment statuses in metadata info in the wrapped deployment object to allow to start a new deployment with this metatada
    """

    # Lists of fields have to be clear to allow to start a new deployment
    clearedFieldsFromRunningDeployment = [
        "status",
        "conditions",
        "metadata.managed_fields",
        "creation_timestamp",
        "generation",
        "metadata.resource_version",
        "self_link",
        "uid",
        "local_vars_configuration",
        "metadata.uid"
    ]

    def _setDeploymentMetadata(self):
        self._deployment.metadata.name = self._name
        self._deployment.metadata.namespace = self._namespace

    # update object attribute if field has hierarchy schema
    @staticmethod
    def _updateMetadataAttr(object, field, value):
        fieldPath = field.split(".")
        obj = object
        for item in fieldPath[:-1]:
            obj = getattr(obj, item)
        setattr(obj, fieldPath[-1], value)

    def _clearStatusInfo(self):
        if self._deployment is not None:
            for item in KubeDeploymentMetadataMixin.clearedFieldsFromRunningDeployment:
                KubeDeploymentMetadataMixin._updateMetadataAttr(self._deployment, item, None)
        return self._deployment

    def _getDeploymentImage(self):
        return self._deployment.spec.template.spec.containers[0].image

    def _setDeploymentImage(self, image):
        self._deployment.spec.template.spec.containers[0].image = image

    def _getDeploymentEnv(self):
        return self._deployment.spec.template.spec.containers[0].env

    def _getDeploymentImagePatch(self, image):
        container_name = self._deployment.spec.template.spec.containers[0].name
        return KubeDeploymentTemplates.buildImagePatch(container_name, image)

    def _getDeploymentEnvPatch(self, item):
        container_name = self._deployment.spec.template.spec.containers[0].name
        return KubeDeploymentTemplates.buildEnvPatch(container_name, item)

    def _getDeploymentNamePatch(self, name):
        return KubeDeploymentTemplates.buildNamePatch(name)

    def _getDeploymentScalePatch(self, replicas):
        return KubeDeploymentTemplates.buildScalePatch(replicas)



class KubeDeploymentManager(KubeDeployment, KubeDeploymentMetadataMixin, KubeDeploymentReplicasMixin):

    def createDeployment(self, deployment=None) -> AKubeDeployment:
        if deployment is not None:
            self._setDeployment(deployment)
        return self._setDeployment(self._getKubeEngine().createDeployment(self._getDeployment(), self._getNameSpace()))

    def scaleReplicas(self, replica_count) -> AKubeDeployment:
        return self.patchDeployment(self._getDeploymentScalePatch(replica_count))

    def patchDeployment(self, patch_body):
        return self._setDeployment(
            self._getKubeEngine().patchDeployment(self.getName(), self._getNameSpace(), patch_body))

    def _resetDeployment(self) -> AKubeDeployment:
        self._clearStatusInfo()
        self._setDeploymentMetadata()
        self.setReplicasCount(0)
        return self


#
# Class for managing clones of the deployment
# react on change configuration and count of main deployment replicas
# We need get from main deploy:
# - image
# - number of replicas
#

class KubeDeploymentWithClone(KubeDeploymentManager, KubeEventHandlerInterface):

    def __init__(self, name, namespace, name_suffix, cloned_factor, image=None, env=None):
        KubeDeployment.__init__(self, name, namespace)
        self._cloned:KubeDeploymentManager = None
        self._cloned_image = image
        self._cloned_env_ext = env
        self._name_suffix = name_suffix
        self._setClonedFactor(cloned_factor)
        self._active_deployment = None
        self._loadClonedDeployment()

    def _loadClonedDeployment(self):
        self._refreshDeploymentInfo()
        if self._deployment is not None:
            self._logger.info("Load cloned deployment from  %s " % self._name)
            cloned_image = self._cloned_image if self._cloned_image is not None else self._getDeploymentImage()  # We can use another image for the clone
            self._cloned = KubeDeploymentManager(self._getClonedName(), self._namespace, cloned_image)
            self._cloned._setDeployment(self._cloned.readDeployment())
            self.update()
        else:
            self._cloned = KubeDeploymentManager(self._getClonedName(), self._namespace)
            self._cloned._refreshDeploymentInfo()
            if self._cloned._deployment is not None:
                self._logger.warning("Resetting old cloned deployment %s " % self._cloned._name)
                self._resetClonedDeployment()
            self._logger.warning("No deployment found %s " % self._name)

    def _getClonedName(self, name=None, suffix=None):
        return self._buildClonedName(self._name, self._name_suffix)

    def _buildClonedName(self, name=None, suffix=None):
        return '{}-{}'.format(name, suffix)

    def _setClonedFactor(self, cloned_factor):
        self._cloned_factor: float = float(cloned_factor)

    def _buildClonedDeployment(self):
        self._setDeployment(self.readDeployment())
        self._cloned._setDeployment(self.getDeployment())._resetDeployment()
        self._cloned.setReplicasCount(self._getRequiredReplicaCount())
        if self._cloned_image is not None:
            self._cloned._setDeploymentImage(self._cloned_image)
        return self

    def _createClonedDeployment(self):
        cloned = self._cloned.getDeployment()
        self._buildClonedDeployment()
        if cloned is None:
            self._cloned.createDeployment()
        else:
            self._cloned.patchDeployment(self._cloned.getDeployment())
        return self

    def _getRequiredReplicaCount(self) -> int:
        try:
            self._setDeployment(self.readDeployment())
            return ceil(self._cloned_factor * self.getReplicasCount())
        except Exception as e:
            self._logger.exception(e)
            return 0

    def _isUpdateConditon(self):
        self._refreshDeploymentInfo()
        return self._cloned.getDeployment() is None or self._cloned.getReplicasCount() != self._getRequiredReplicaCount()

    def _isRecreateCondition(self, new_config: DeploymentConfigDto):
        if self._buildClonedName(new_config.body.get('name'),
                                 new_config.body.get('name_suffix')) != self._cloned.getName():
            return True
        if self._cloned._getDeploymentImage() != new_config.body.get('cloned_image'):
            return True
        return False

    def update(self):
        if not self._cmpDeployments(self.getDeployment(), self._active_deployment):             # if deployment was updated
            self._createClonedDeployment()                                                      # create/update a clone object
            self._active_deployment = self._getDeployment()
        if self._isUpdateConditon():                                                            # if replicas count changed
            self._scaleClonedDeployment()
            self._active_deployment = self._getDeployment()

    def healthCheck(self):
        return not self._isUpdateConditon()

    def _scaleClonedDeployment(self) -> AKubeDeployment:
        if self._cloned.getDeployment() is None:
            # if self._getRequiredReplicaCount() == 0:      TODO: In future don't create profiler if replicas == 0
            #     return None
            self._createClonedDeployment()
        return self._cloned.scaleReplicas(self._getRequiredReplicaCount())

    def _resetClonedDeployment(self):
        if self._cloned.getDeployment() is not None:
            return self._cloned.scaleReplicas(0)

    # This function called when a deployment changed
    def eventHandler(self, event):
        try:
            if event['type'] == 'MODIFIED' and event['object'].metadata.name == self._name:
                if self._deployment is None:
                    self._loadClonedDeployment()
                if self._deployment is not None:
                    self.update()
        except Exception as e:
            self._logger.exception(e)

    # This function called when a configmap changed and updates this deployment according to the configmap
    # we can check clone name, clone image, patched environment variable, scale factor
    def updateClonedDeploymentConfig(self, new_config: DeploymentConfigDto):
        if new_config.name == self._name:
            self._logger.debug("Deployment clone %s is updating" % new_config.name)
            if self._deployment is None:
                self._loadClonedDeployment()
            if self._deployment is not None:
                self._runIfClonesNameChanged(new_config)                        # If cloned deployment name chamged
                self._updateClonedImageConfig(new_config)                       # If there is cloned_image configuration
                self._updateClonedEnvConfig(new_config)                         # If there is an env variable in configuration
                self._setClonedFactor(new_config.body.get('scale_factor', 0))
                self._name_suffix = new_config.body.get('name_suffix', 'clone')
                # self._image = new_config.body.get('image', None)
                self.update()

    #
    # If cloned name was changed
    # updatet existing cloned deployment
    #
    def _runIfClonesNameChanged(self, new_config):
        if self._buildClonedName(new_config.name,
                                 new_config.body.get('name_suffix', 'clone')) != self._cloned.getName():
            patch = self._cloned._getDeploymentNamePatch(
                self._buildClonedName(new_config.name, new_config.body.get('name_suffix', 'clone')))
            self._cloned.patchDeployment(patch)

    #
    # If cloned image is not the same as original
    # replace that one from configmap
    #
    def _updateClonedImageConfig(self, new_config):
        if new_config.body.get('cloned_image', None) is not None and self._cloned._getDeploymentImage() != new_config.body.get(
                'cloned_image'):
            patch = self._cloned._getDeploymentImagePatch(new_config.body.get('cloned_image'))
            self._cloned.patchDeployment(patch)

    #
    # If cloned configuration has env section
    # add env variable to cloned
    # only one environment variable allowed
    #
    def _updateClonedEnvConfig(self, new_config):
        if new_config.body.get('env', None) is not None:
            env_var = new_config.body.get('env').replace(' ', '').split(':')
            env_val = KubeDeploymentTemplates. \
                findEnvInListEnv(self._cloned._getDeploymentEnv(),
                                 new_config.body.get('env').replace(' ', '').split(':')[0])
            if env_val is None or env_val.value != env_var[1]:
                patch = self._cloned._getDeploymentEnvPatch(env_var)
                self._cloned.patchDeployment(patch)

    def _cmpDeployments(self, sourceDeployment, targetDeployment):
        return sourceDeployment.metadata.resource_version == targetDeployment.metadata.resource_version if targetDeployment is not None else False



