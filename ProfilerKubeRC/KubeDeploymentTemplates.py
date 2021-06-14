#
# Set of templates for patching kubernetes objects
# These templates depended on version of kubernetes object
#


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
