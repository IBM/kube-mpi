There are 3 yaml files for launching simple hello world example:

1. mpiapp-hostnet.yaml.icp
2. mpiapp-hostnet.yaml.ocp
3. mpiapp-podnet.yaml


The files are customized for executing on an OCP or a ICP cluster.

The build-hello.sh script takes a command line argument, ICP, to build the example with the tag for the ICP internal docker registry. The default is to build for the OCP internal registry.

The example/dockerfiles/Dockerfile must be modified to switch from ICP to OCP or vice versa. The two base image choices for the base mofed image are listed in the Dockerfile
