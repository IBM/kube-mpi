#!/bin/bash
tag="default-route-openshift-image-registry.apps.foc.foccluster.com/default/hello:1.0"
docker rmi -f $(docker images | egrep "hello" | awk '{print $3}')
cp /home/damora/.ssh/id_rsa dockerfiles/
docker build --no-cache --compress  --rm -t $tag -f dockerfiles/Dockerfile dockerfiles/ 
#docker build --no-cache --compress --squash --rm -t dcscloud.icp:8500/default/bddhello:centos -f dockerfiles/Dockerfile .
#docker build -t dcscloud.icp:8500/default/kube-mpi-controller:centos -f dockerfiles/Dockerfile context/ 
#docker build --no-cache --compress --squash --rm -t dcscloud.icp:8500/default/kube-mpi-controller:centos -f dockerfiles/Dockerfile context/  --build-arg bootstrap=bootstrap.job
