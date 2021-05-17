# This file contents of:
# - KubeDeployment          : Base class to work with a deployment object
# - KubeDeploymentViewer    : Class with methods for reading object
# - KubeDeploymentManager   : Class with methods for reading, writing and managing object
# - KubeDeploymentWithClone : Class with its clone
# - AKubeDeployment         : Set of public interfaces with abstract methods to work with a deploy object
# - DeploymentConfigDto     : Object with configuring properties for the deployment
# - KubeDeploymentTemplates : Set templates to patching deployment object


from abc import ABC, abstractmethod
from dependency_injector.wiring import inject, Provide
from math import ceil
from kubernetes.client import V1Deployment

from ProfilerKubeRC.KubeEngine import KubeEngine
from ProfilerKubeRC.KubeEventListener import KubeEventHandlerInterface
from ProfilerKubeRC.container import EngineContainer
from ProfilerKubeRC.logger import LoggerContainer
from ProfilerKubeRC.logger import SLogger

#
# Set of templates for patching kubernetes objects
# These templates depended on version of kubernetes object
#

template_patch_image = {
    "spec": {
        "template": {
            "spec": {
                "containers": [{}]
            }
        }
    }
}

template_patch_name = {
    "metadata": {
        "name": ""
    }
}


class KubeDeploymentTemplates:
    template_patch_image = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [{}]
                }
            }
        }
    }
    template_patch_env = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "env": []
                        }
                    ]
                }
            }
        }
    }
    template_patch_name = {
        "metadata": {
            "name": ""
        }
    }
    scale_body_template = {
        "spec": {
            "replicas": 0
        }
    }

    @staticmethod
    def buildImagePatch(container_name, image):
        template = KubeDeploymentTemplates.template_patch_image.copy()
        template['spec']['template']['spec']['containers'][0]['image'] = image
        template['spec']['template']['spec']['containers'][0]['name'] = container_name
        return template

    @staticmethod
    def buildEnvPatch(container_name, item):
        template = KubeDeploymentTemplates.template_patch_env.copy()
        template['spec']['template']['spec']['containers'][0]['name'] = container_name
        template['spec']['template']['spec']['containers'][0]['env'].append({"name": item[0], "value": item[1]})
        return template

    @staticmethod
    def buildNamePatch(name):
        template = KubeDeploymentTemplates.template_patch_name.copy()
        template['metadata']['name'] = name
        return template

    @staticmethod
    def buildScalePatch(replicas):
        template = KubeDeploymentTemplates.scale_body_template.copy()
        template['spec']['replicas'] = replicas
        return template

    @staticmethod
    def findEnvInListEnv(lst, env):
        if lst is None:
            return None
        for item in lst:
            if env == item.name:
                return item
        return None


class DeploymentConfigDto:
    def __init__(self, name, body):
        self.name = name
        self.body = body


class AKubeDeployment(ABC):

    @abstractmethod
    def eventHandler(self, event):
        pass

    @abstractmethod
    def update(self):
        pass


class KubeDeployment(AKubeDeployment, KubeEventHandlerInterface):
    def __init__(self, name, namespace, image=None):
        self._setLogger()
        self._name = name
        self._image = image
        self._namespace = namespace
        self._setKubeEngine()
        # self._deployment can be None if replicas == 0. It is a reason because I duplicate name, namespace and images with _deployment: V1Deployment

    @inject
    def _setLogger(self, logger: SLogger = Provide[LoggerContainer.logger_svc]):
        self._logger = logger

    @inject
    def _setKubeEngine(self, engine: KubeEngine = Provide[EngineContainer.kube_engine]):
        self._kube_engine = engine

    def _getKubeEngine(self):
        return self._kube_engine

    def _getDeployment(self) -> V1Deployment:
        return self._deployment

    def _setDeployment(self, deployment: V1Deployment):
        self._deployment: V1Deployment = deployment
        return self

    def getName(self) -> str:
        return self._name

    def _setName(self, name):
        self._name = name
        if self._deployment is not None:
            self._deployment.metadata.name = name

    def _getNameSpace(self):
        return self._namespace

    def eventHandler(self, event):
        pass

    def update(self):
        pass

    def getDeployment(self):
        return self._deployment

    def setDeployment(self, deployment):
        self._name = deployment.metadata.name
        self._deployment = deployment
        self._namespace = deployment.metadata.namespace

    def makeDeploymentJson(self, deployment):
        self._deployment = deployment

    def getDeploymentName(self):
        return self._deployment

    def setDeploymentName(self, name):
        self._name = name

    def _setDeploymentMetadata(self):
        self._deployment.metadata.name = self._name
        self._deployment.metadata.namespa = self._namespace

    def getReplicasCount(self) -> int:
        return int(
            self._deployment.status.replicas) if self._deployment is not None and self._deployment.status is not None and self._deployment.status.replicas is not None else 0

    def setReplicasCount(self, replicas):
        if self._deployment is not None:
            self._deployment.spec.replicas = replicas

    def _clearStatusInfo(self):
        if self._deployment is not None:
            self._deployment.status = None
            self._deployment.conditions = None
            self._deployment.metadata.managed_fields = None
            self._deployment.creation_timestamp = None
            self._deployment.generation = None
            self._deployment.metadata.resource_version = None
            self._deployment.self_link = None
            self._deployment.uid = None

            self._deployment.local_vars_configuration = None

        return self._deployment

    def _resetDeployment(self) -> AKubeDeployment:
        self._clearStatusInfo()
        self._setDeploymentMetadata()
        self.setReplicasCount(0)
        return self

    def cloneDeploymentJson(self, src):
        self.setDeployment(src)

    def _getDeploymentImage(self):
        return self._deployment.spec.template.spec.containers[0].image

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


class KubeDeploymentViewer(KubeDeployment):

    def readDeployment(self) -> V1Deployment:
        return self._getKubeEngine().readDeployment(self.getName(), self._getNameSpace())


class KubeDeploymentManager(KubeDeploymentViewer):

    def createDeployment(self, deployment=None) -> AKubeDeployment:
        if deployment is not None:
            self._setDeployment(deployment)
        return self._setDeployment(self._getKubeEngine().createDeployment(self._getDeployment(), self._getNameSpace()))

    def scaleReplicas2(self, replica_count) -> AKubeDeployment:
        self.setReplicasCount(replica_count)
        return self._setDeployment(
            self._getKubeEngine().scaleReplica(self.getName(), self._getNameSpace(), replica_count))

    def scaleReplicas(self, replica_count) -> AKubeDeployment:
        return self.patchDeployment(self._getDeploymentScalePatch(replica_count))

    def patchDeployment(self, patch_body):
        return self._setDeployment(
            self._getKubeEngine().patchDeployment(self.getName(), self._getNameSpace(), patch_body))


class KubeDeploymentWithClone(KubeDeploymentManager):

    def __init__(self, name, namespace, name_suffix, cloned_factor, image=None):
        KubeDeployment.__init__(self, name, namespace)
        self._cloned_image = image
        self._name_suffix = name_suffix
        self._setClonedFactor(cloned_factor)
        self._setDeployment(self.readDeployment())
        cloned_image = image if image is not None else self._getDeploymentImage()
        self._cloned = KubeDeploymentManager(self._getClonedName(), namespace, cloned_image)
        self._cloned._setDeployment(self._cloned.readDeployment())
        self.update()

    def _getClonedName(self, name=None, suffix=None):
        return self._buildClonedName(self._name, self._name_suffix)

    def _buildClonedName(self, name=None, suffix=None):
        return '{}-{}'.format(name, suffix)

    def _setClonedFactor(self, cloned_factor):
        self._cloned_factor: float = float(cloned_factor)

    def _createClonedDeployment(self):
        self._setDeployment(self.readDeployment())
        self._cloned._setDeployment(self.getDeployment())._resetDeployment()
        self._cloned.createDeployment()
        return self

    def _getRequiredReplicaCount(self) -> int:
        try:
            self._setDeployment(self.readDeployment())
            return ceil(self._cloned_factor * self.getReplicasCount())
        except Exception as e:
            self._logger.exception(e)
            return 0

    def _isUpdateConditon(self):
        return self._cloned.getDeployment() is None or self._cloned.getReplicasCount() != self._getRequiredReplicaCount()

    def _isRecreateCondition(self, new_config: DeploymentConfigDto):
        if self._buildClonedName(new_config.body.get('name'),
                                 new_config.body.get('name_suffix')) != self._cloned.getName():
            return True
        if self._cloned._getDeploymentImage() != new_config.body.get('image'):
            return True
        return False

    def update(self):
        if self._isUpdateConditon():
            self._scaleClonedDeployment()

    def _scaleClonedDeployment(self) -> AKubeDeployment:
        if self._cloned.getDeployment() is None:
            # if self._getRequiredReplicaCount() == 0:      TODO: In future don't create profiler if replicas == 0
            #     return None
            self._createClonedDeployment()
        return self._cloned.scaleReplicas(self._getRequiredReplicaCount())

    def eventHandler(self, event):
        try:
            if event['type'] == 'MODIFIED' and event['object'].metadata.name == self._name:
                self.update()
        except Exception as e:
            self._logger.exception(e)

    def updateDeploymentConfig(self, new_config: DeploymentConfigDto):
        if new_config.name == self._name:
            self._logger.debug("Deployment clone %s is updating" % new_config.name)
            if self._buildClonedName(new_config.name,
                                     new_config.body.get('name_suffix', 'clone')) != self._cloned.getName():
                patch = self._cloned._getDeploymentNamePatch(
                    self._buildClonedName(new_config.name, new_config.body.get('name_suffix', 'clone')))
                self._cloned.patchDeployment(patch)
            if new_config.body.get('image',
                                   None) is not None and self._cloned._getDeploymentImage() != new_config.body.get(
                    'image'):
                patch = self._cloned._getDeploymentImagePatch(new_config.body.get('image'))
                self._cloned.patchDeployment(patch)
            if new_config.body.get('env', None) is not None:
                # envList = self._cloned._getDeploymentEnv()
                # var = new_config.body.get('env')
                # env_var = var.replace(' ', '').split(':')
                # env_val = KubeDeploymentTemplates.findEnvInListEnv(self._cloned._getDeploymentEnv(), env_var[0])
                env_var = new_config.body.get('env').replace(' ', '').split(':')
                env_val = KubeDeploymentTemplates. \
                    findEnvInListEnv(self._cloned._getDeploymentEnv(),
                                     new_config.body.get('env').replace(' ', '').split(':')[0])
                if env_val is None or env_val.value != env_var[1]:
                    patch = self._cloned._getDeploymentEnvPatch(env_var)
                    self._cloned.patchDeployment(patch)

            self._setClonedFactor(new_config.body.get('scale_factor', 0))
            self._name_suffix = new_config.body.get('name_suffix', 'clone')
            self._image = new_config.body.get('image', None)
            self.update()
