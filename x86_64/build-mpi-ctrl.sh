#!/bin/bash
VERSION=1.0
PROJECT=default
HOST=$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}')
podman login -u $(oc whoami) -p $(oc whoami -t) --tls-verify=false $HOST
tag="$HOST/$PROJECT/mpi-ctrl:$VERSION"
cp ~/.ssh/id_rsa* dockerfiles/
podman  rmi -f $(docker images | egrep "mpi-ctrl" | awk '{print $3}')
podman  build  --rm -t $tag -f dockerfiles/Dockerfile.ctrl dockerfiles/
