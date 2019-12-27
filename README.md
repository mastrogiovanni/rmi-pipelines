# rmi-pipelines
A Study on Distributed Pipelines for RMI

# Architecture

The architecture to distribute RMI workload is the following:
- Kubernetes private docker registry to push temporary artifacts and to pull images for Kubernetes cluster,
- Jupyther notebook on base OS to launch computations,
- Minio in the cluster as S3 object storage for files and artifacts passed between workflows steps,
- Argo Workflow to manage pipelines in Kubernetes cluster.


# Setup

In order to setup the system you need to install microk8s (Ubuntu).
This is the only system where this software was tested.

## Microk8s

You need to install microk8s:

> sudo snap install microk8s --classic

Microk8s modules required for the demo are:
- dns: naming resolution inside kubernetes
- storage: default storage class that aim to save locally persistent volumes
- registry: Internal registry to save local images
- helm: Package manager for Kubernetes

You can install them with the following:

> microk8s.enable dns storage registry helm

## Argo Workflow

Argo is the workflow engine for Kubernetes. 
It supports storage, parameters and artifacts passing and many workflows configuration.

Create a namespace for Argo controller:

> kubectl create namespace argo

Install Argo controller and UI:

> kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/stable/manifests/install.yaml

## Minio

Install Minio via helm (username: *minioadmin*, password: *minioadmin*)
(https://github.com/helm/charts/tree/master/stable/minio):

> microk8s.helm install --name minio --set accessKey=minioadmin,secretKey=minioadmin --set ingress.enabled=true stable/minio

Find the minio pod:

> export POD_NAME=$(kubectl get pods --namespace default -l "release=minio" -o jsonpath="{.items[0].metadata.name}")

Expose minio on the local base OS:

> kubectl port-forward $POD_NAME 9000 --namespace default

You can access to minio UI via URL: http://127.0.0.1:9000

# Default artifact repository

IN order to work with notebooks and with Argo you need to setup the standard artifact repository.
For our study we use the S3 compliant storage provided by minio.
In order to setup this default artifact storage you need to edit the Argo Controller's ConfigMap (https://github.com/argoproj/argo/blob/master/docs/configure-artifact-repository.md) with endpoints and Minio Credentials.

First inject Minio credentials in a Kubernetes secret:

> kubectl create secret generic s3-secret --from-literal=accessKey=minioadmin --from-literal=secretKey=minioadmin

Than edit Argo Controller to setup default artifact repository:

> kubectl edit cm workflow-controller-configmap -n argo

and add the *data* section:

```
data:
  config: |
    artifactRepository:
      s3:
        bucket: subjects-data
        endpoint: minio.default:9000
        insecure: true
        accessKeySecret:
          name: s3-secret
          key: accessKey
        secretKeySecret:
          name: s3-secret
          key: secretKey
```

Remember to kill argo controller to restart it with new configuration:

> kubectl delete -n argo $(kubectl get pods -n argo -l "app=workflow-controller" -o jsonpath="{.items[0].metadata.name}")

# Problems

microk8s has a problem in management of serialization given its runtime (https://github.com/kubeflow/pipelines/issues/1471).
In order to solve the problem you need to change the docker container runtime of the microk8s kubelet

in file: `/var/snap/microk8s/current/args/kubelet`
```
# --container-runtime=remote
# --container-runtime-endpoint=${SNAP_COMMON}/run/containerd.sock
--container-runtime=docker
```

And restart it:

> sudo systemctl restart snap.microk8s.daemon-kubelet.service

# Resources

Minio UI: http://localhost:9000
Python Objects for argo-workload: https://github.com/CermakM/argo-client-python/tree/master/docs
Argo examples: https://argoproj.github.io/docs/argo/examples/readme.html





