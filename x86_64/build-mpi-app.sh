#!/bin/bash
export VERSION=5.4-1.0.3.0
PROJECT=default
HOST=$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}')
podman login -u $(oc whoami) -p $(oc whoami -t) --tls-verify=false $HOST
tag="$HOST/$PROJECT/mofed:${VERSION}"

podman  rmi -f $(docker images | egrep "mofed" | awk '{print $3}')
podman  build --rm -t $tag  -f dockerfiles/Dockerfile.app dockerfiles/
#docker build --no-cache --compress --rm -t $tag  -f dockerfiles/Dockerfile.app dockerfiles/
