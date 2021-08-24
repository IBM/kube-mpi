FROM default-route-openshift-image-registry.apps.foc.foccluster.com/default/mofed:5.4-1.0.3.0

WORKDIR /


COPY hello.c /
RUN  mpicc hello.c -o hello
