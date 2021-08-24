# kube-mpi-ctrl
Proposed MPI controller for launching MPI jobs in kubernetes
# Instructions to build
1. Configure so that "kubectl" will work to the right ICp system, by cutting-and-pasting the configuration commands from the ICp web interface.
1. Download and unpack the MOFED tarball.

   You should use the same level of MOFED in the container as is installed on the real systems. MOFED drivers can be downloaded from [http://www.mellanox.com/page/products_dyn?product_family=26](http://www.mellanox.com/page/products_dyn?product_family=26)

   Unpack the tarball into the kube-mpi-ctrl/context directory.
1. Edit kube-mpi-ctrl/build-mpi-app.sh to make the name agree with the unpacked tarball.
1. Run build-mpi-app.sh
1. Run "docker push dcscloud.icp:8500/default/mofed:4.7-1.0.0.1"
1. Run build-mpi-ctrl.sh
1. Run "docker push dcscloud.icp:8500/default/mpi-ctrl:centos"
1. Go to the "apps" directory
1. Run build-phloem.sh
1. Run "docker push dcscloud.icp:8500/default/tjcwphloem:centos"

# Instructions to run
1. In the apps directory, run a command such as "subctlappjob.sh tjcw-presta-ctl tjcw-presta-app phloem-presta.yaml.template"

   This submits a controller job "tjcw-presta-ctl" and an MPI job "tjcw-presta-app" using the given YAML template file. "presta" is a point-to-point bandwidth test using 2 nodes.
1. Run "kubectl get pods -l job=tjcw-presta-ctl" to find the pod that is running the controller job
1. Run "kubectl logs -f tjcw-presta-ctl-xxxxx" to get the job log. Replace "xxxxx" with the pod name suffix from the "get pods" command. This will include the stdout and stderr from the mpirun command when the mpirun finishes.
1. Run "kubectl get pods -l job=tjcw-presta-app" to check the status of the pods running the application.
1. When the job has completed, run "kubectl delete job tjcw-presta-app" and "kubectl delete job tjcw-presta-ctl" to clean up the Kubernetes resources.

