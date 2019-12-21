#!/bin/bash

docker run -d \
	--name rmi-notebook \
	--rm \
	--user "$(id -u $USER):$(id -g $USER)" \
	-v $(pwd):/home/jovyan \
	-v /usr/local/freesurfer:/usr/local/freesurfer \
	-v /usr/local/fsl:/usr/local/fsl \
	-v /data/MASTROGIOVANNI:/data/MASTROGIOVANNI \
	-p 18888:8888 \
	mastrogiovanni/rmi-notebook

# 	jupyter/datascience-notebook

