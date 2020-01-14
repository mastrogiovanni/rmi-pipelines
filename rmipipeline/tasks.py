from argo.workflows.client.models import *
from argo.workflows.client import V1alpha1Api
from argo.workflows.config import load_kube_config

"""
Task
"""
class Task:
    
    def __init__(self, name, image, command=None, arguments=[]):
        self.name = name
        self.image = image
        self.command = command
        self.arguments = arguments
        self.parents = []
        self.volumes = []
        
    def getContainer(self):
        return V1Container(
            name=self.name, 
            image=self.image,
            command=self.command,
            args=self.arguments,
            volume_mounts=self.volumes
        )

    def mountVolumeAt(self, name, path):
        self.volumes.append(
            V1VolumeMount(
                name=name,
                mount_path=path
            )
        )

    def set_upstream(self, task):
        self.parents.append(task)
        return task
    
    def __str__(self):
        return f"{self.name} {self.image} {self.parents}"

"""
Bash is a particular container that allows to launch bash scripts in ubuntu OS
"""
class Bash(Task):
    def __init__(self, name, command=None, arguments=[]):
        super().__init__(name, "ubuntu", command, arguments)
        
"""
FreeSurfer is a container that allows to send FreeSurfer commands.
It mountw the license file in /opt/freesurfer.
The license file must be in ConfigMap called freesurfer-license.
"""
class FreeSurfer(Task):
    
    def __init__(self, name, command):
        super().__init__(name, "freesurfer/freesurfer:6.0", command.split(" "), [])
        self.volumes.append(V1VolumeMount(
            name="freesurfer-license",
            mount_path="/opt/freesurfer/license.txt",
            sub_path="license.txt"
        ))
    
"""
Pipeline is a set of tasks that are executed in a given order.
Task can share files or mount external file systems.
"""
class Pipeline():
    
    def __init__(self, namespace='default'):
        self.tasks = []
        self.namespace = namespace
        self.volumes = []
        
    def add(self, task):
        self.tasks.append(task)
        return task
    
    def run(self):
        workflow = self.__get_workflow(self.tasks)
        load_kube_config()  # loads local configuration from ~/.kube/config
        v1alpha1 = V1alpha1Api()
        return v1alpha1.create_namespaced_workflow(self.namespace, workflow)
    
    def exposeClaimWithName(self, name):
        self.volumes.append(V1Volume(
            name=name,
            persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
                claim_name=name
            )
        ))
                            
    def __create_dag(self, task_list):

        tasks = []

        for task in task_list:

            dependencies = []
            for p in task.parents:
                dependencies.append("dag-" + p.name)

            task_argo = V1alpha1DAGTask(
                name="dag-" + task.name, 
                template=task.name,
                dependencies=dependencies)

            tasks.append(task_argo)

        return V1alpha1DAGTemplate(tasks=tasks)

    def __get_workflow(self, task_list): 
        
        templates = []
        roots = []
        for task in task_list:
            
            container = task.getContainer()
            
            template = V1alpha1Template(
                name=task.name, 
                container=container)
            
            templates.append(template)
            
            if len(task.parents) == 0:
                roots.append(task)

        # Root tasks
        if len(roots) == 1:

            root_task = roots[0]

            templates.append(V1alpha1Template(
                name="dag-" + root_task.name, 
                dag=self.__create_dag(task_list)))
            
            # Expose License ConfigMap to be used by FreeSurfer tasks
            # License Config Map: to be added only if FreeSurfer task exists
            self.volumes.append(V1Volume(
                name="freesurfer-license",
                config_map=V1ConfigMapVolumeSource(
                    name="freesurfer-license"
                )
            ))

            spec = V1alpha1WorkflowSpec(
                entrypoint="dag-" + root_task.name, 
                templates=templates,
                volumes=self.volumes)

            workflow = V1alpha1Workflow(
                api_version="argoproj.io/v1alpha1",
                kind="Workflow",
                metadata=V1ObjectMeta(generate_name="dag-diamond-"), 
                spec=spec,
                status=V1alpha1WorkflowStatus())    

        return workflow