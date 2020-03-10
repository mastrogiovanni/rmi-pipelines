#!/bin/bash

argo list | awk -F " " '{print $1}' | tail -n +2 | xargs -n 1 argo delete


