import uuid
from kubernetes import client, config
from argo.workflows.client.models import *
import kubernetes

"""
ReadWriteOnce – the volume can be mounted as read-write by a single node
ReadOnlyMany – the volume can be mounted read-only by many nodes
ReadWriteMany – the volume can be mounted as read-write by many nodes
"""
def create_local_storage(coreV1Api, name, namespace, path, size, mode):
    
    STORAGE_CLASS_NAME = "manual"
    
    unique_name = name + "-" + str(uuid.uuid1())[:8]
    
    try:
        api_response = coreV1Api.create_persistent_volume(
            V1PersistentVolume(
                metadata=V1ObjectMeta(
                    name=unique_name,
                    labels={
                        "uuid": unique_name
                    }
                ),
                spec=V1PersistentVolumeSpec(
                    storage_class_name=STORAGE_CLASS_NAME,
                    capacity={
                        "storage": size
                    },
                    access_modes=[mode],
                    host_path=V1HostPathVolumeSource(
                        path=path
                    )
                )
            )    
        )
        # pp.pprint(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_persistent_volume_claim: %s\n" % e)

    try:
        coreV1Api.create_namespaced_persistent_volume_claim(
            namespace=namespace,
            body=V1PersistentVolumeClaim(
                metadata=V1ObjectMeta(
                    name=unique_name,
                    labels={
                        "uuid": unique_name
                    }
                ),
                spec=V1PersistentVolumeClaimSpec(
                    storage_class_name=STORAGE_CLASS_NAME,
                    access_modes=[mode],
                    volume_mode="Filesystem",
                    resources=V1ResourceRequirements(
                        requests={
                            "storage": size
                        }
                    ),
                    selector=V1LabelSelector(
                        match_labels={
                            "uuid": unique_name
                        }
                    )
                )
            )
        )
        # pp.pprint(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_persistent_volume_claim: %s\n" % e)
        
    return unique_name

"""
Delete all PersistentVolume and PersistentVolumeClaims starting with given name in a namespace.
This method can be used to remove any occurrence of the Volume created via create_local_storage method
"""
def delete_all_pv_and_pvc(client, name, namespace):
    
    count_pv = 0
    count_pvc = 0
    
    # Delete Persistent Volumes
    result = client.list_persistent_volume()
    for pv in filter(lambda x: x.startswith(name), map(lambda x: x.metadata.name, result.items)):
        client.delete_persistent_volume(name=pv)
        count_pv = count_pv + 1
    
    # Delete Persistent Volume Claims
    result = client.list_namespaced_persistent_volume_claim(namespace=namespace)
    for pvc in filter(lambda x: x.startswith(name), map(lambda x: x.metadata.name, result.items)):
        client.delete_namespaced_persistent_volume_claim(name=pvc, namespace=namespace)
        count_pvc = count_pvc + 1
        
    print(f"Deleted {count_pv} PersistentVolumes and {count_pvc} PersistentVolumeClaims")

    