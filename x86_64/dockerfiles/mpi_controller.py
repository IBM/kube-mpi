#!/usr/bin/env python
from collections import OrderedDict
from kubernetes import client,config
from kubernetes.client.models.v1_pod_spec import V1PodSpec
from kubernetes.stream import stream
import os
import json
import time
import subprocess
import sys
#import gflags
from absl import flags
import netifaces
import netaddr
from netaddr import *
import socket, struct
from pkg_resources import get_distribution, DistributionNotFound

__project__ = 'kubernetes'

try:
    __version__ = get_distribution(__project__).version
except DistributionNotFound:
    __version__ = None

print("version= " + __version__)

namespace = os.environ['NAMESPACE']
print ("namespace: " + namespace)
FLAGS = flags.FLAGS
flags.DEFINE_string('cmd', '/pi 0.001', 'cmd to start the mpi job')
flags.DEFINE_string('job_name', 'job', 'name of the job')
flags.DEFINE_string('network', '9.2.132.202/16', 'network to run job on')
flags.DEFINE_string('mpi_args', '', 'Extra arguments to mpirun')
flags.DEFINE_string('app_args', '', 'Arguments to the application')
flags.DEFINE_integer('ppn', 1, 'Processes per node')



config.load_incluster_config()
v1 = client.CoreV1Api()
v1batch=client.BatchV1Api()


frequency = 10

def getPodIpStr(namespace, job_name, ppn):
    hostStr = ""
    sep=''
    nsep=''
    nhostStr=""

    isMaster = False
    ps_pods = v1.list_namespaced_pod(namespace, label_selector="job=" +
                                     job_name)
    job = v1batch.list_namespaced_job(namespace, label_selector="job=" +
                                      job_name)
    worker_num = job.items[0].spec.parallelism
    items = ps_pods.items

    print("items=  ", len(items))
    print("worker_num=  " + str(worker_num))

    if (len(items) < worker_num):
        return False, "", False

    print(items)
    for i in range(0, len(items)):
        try:
            podIp = items[i].status.pod_ip
            print("podIp:" + podIp)
#            print("localIp:" + localIp)
#            if (i == 0 and podIp == localIp):
#                isMaster = True
            hostStr = hostStr + sep + podIp
            sep = ',' 
            for j in range(ppn):
                nhostStr=nhostStr + nsep + podIp
                nsep=','
        except Exception as err:
            return False, "", isMaster, 0
    return True, hostStr, nhostStr, isMaster, len(items)

def getHostIpStr(namespace, job_name, ppn):

    hostlist = []
    hostIPs = ""
    hostNames = ""
    nhostNames = ""
    podIp = ""

    sep = ""
    nsep = ""

    ready    = True     # ready to start mpi
    isMaster = False    # is root
    podCount = 0        # number of pods in ijob

    # get pods, job, and expected number of workers
    pods    = v1.list_namespaced_pod(namespace, label_selector="job="  + job_name).items
    job     = v1batch.list_namespaced_job(namespace, label_selector="job=" + job_name).items[0]
    workers = job.spec.parallelism

    containers = pods[0].spec.containers
    for container in containers :
        print container.name

    for i in range(len(pods)):

        # add a basic pod name based filter        
        pod_name = pods[i].metadata.name
        job_name = job.metadata.name
        if not pod_name.startswith(job_name):
            print 'ignored pod "%s"' % (pod_name)
            continue

        podCount=podCount+1 

        # if number of active pods < total, job is not ready
        if job.status.active < workers:
            print 'only %d out of %d pods are ready; wait' % (\
                    job.status.active, 
                    workers)
            ready = False
            break

        podIp = pods[i].status.pod_ip
        print 'add pod "%s" (pod_ip="%s")' % (\
                pod_name, 
                podIp)

#        if (i == 0 and podName == pods[i].metadata.name):
#            isMaster = True
        hostlist.append(pod_name)
        hostIPs=hostIPs+sep+podIp
        hostNames=hostNames+sep+pod_name
        sep=","
        for j in range(ppn):
            nhostNames=nhostNames+nsep+pod_name
            nsep=','

    return ready, hostNames, nhostNames, isMaster, podCount

def waitForJob(job_name):
    while True:
        ret = v1batch.list_job_for_all_namespaces(watch=False)
        for job in ret.items:
            if job.metadata.name == job_name:
                return
        print("Waiting for job " + job_name + " to start.")
        time.sleep(frequency)

def main():
    print("--------------------------\n") 
    print("MPI controller started...")
    print("--------------------------\n") 
    print(sys.argv)
    FLAGS(sys.argv)
    print ("FLAGS.job_name: " + FLAGS.job_name)
    print ("FLAGS.cmd: " + FLAGS.cmd)
    print ("FLAGS.network: " + FLAGS.network)
    print ("FLAGS.mpi_args: " + FLAGS.mpi_args)
    print ("FLAGS.app_args: " + FLAGS.app_args)
    print ("FLAGS.ppn: " + str(FLAGS.ppn))

    ppn=FLAGS.ppn

    hostNetwork = True
    waitForJob(FLAGS.job_name)
    masterPod = None
    masterJob = None
    ret = v1batch.list_namespaced_job(namespace,watch=False)
    label_selector =  'job=' + FLAGS.job_name # job-name=argument in pod spec
    print("label_selector=" + label_selector + "\n") 
    for job in ret.items:
        print("job namespace = %s\t job name = %s" %(job.metadata.namespace, job.metadata.name))
        if job.metadata.name != FLAGS.job_name:
            print("Job ",job.metadata.name, "not mine, continuing")
            continue
        waiting = True
        while waiting:
            print("list_namespaced_pod(",job.metadata.namespace,",label_selector=",label_selector,")")
            allPods = v1.list_namespaced_pod(job.metadata.namespace,label_selector=label_selector,watch=False)
            waiting = False
            for pod in allPods.items:
                if masterPod == None:
                    masterPod = pod
                    masterJob = job 
                print("%s\t%s" %( pod.metadata.namespace, pod.metadata.name))
                print(pod.status.phase)
                if pod.status.phase != 'Running':
                    waiting = True
                    print("still waiting for pod %s to be running" %(pod.metadata.name))
                    time.sleep(frequency)
                    break            
                elif pod.status.phase == 'Running':
                    print("pod %s running" %(pod.metadata.name))

    if masterPod != None:
        print("\nRunning exec in pod %s" %(masterPod.metadata.name))
        if hostNetwork:
            isParamReady,hostList,nhostList,isMaster,podCount = getHostIpStr(masterJob.metadata.namespace, masterJob.metadata.name,ppn) ;
            exec_command = [
                 'mpirun',
                 '--allow-run-as-root',
                 '-mca','plm_rsh_agent','kssh',
                 '-mca','btl_tcp_if_include',FLAGS.network,
                 '-x','UCX_NET_DEVICES=mlx5_0:1',
                 '-map-by','core',
                 '-n',str(podCount*ppn),
                 '-x','MXM_IB_PORTS=mlx5_0:0',
                 '-host', nhostList] + FLAGS.mpi_args.split() + [
                 FLAGS.cmd
              ] + FLAGS.app_args.split()
            flag_command = [
                 'mpirun',
                 '--allow-run-as-root',
                 '-mca','plm_rsh_agent','kssh',
                 '-mca','btl_tcp_if_include',FLAGS.network, 
                 '-x','UCX_NET_DEVICES=mlx5_0:1',
                 '-map-by','core',
                 '-n',str(podCount),
                 '-x','MXM_IB_PORTS=mlx5_0:0',
                 '-host', hostList,
                 'touch',
                 './appflag'
              ]
        else:
            isParamReady,hostList,nhostList,isMaster,podCount = getPodIpStr(masterJob.metadata.namespace, masterJob.metadata.name,ppn) ; 
            exec_command = [
                 'mpirun',
                 '--allow-run-as-root',
                 '-mca','oob','tcp',
                 '-mca','pml','ob1',
                 '-mca','btl','tcp,vader,self',
                 '-n',str(podCount*ppn),
#                 '-x','MXM_IB_PORTS=mlx5_0:0',
                 '-host', nhostList] + FLAGS.mpi_args.split() + [
                 FLAGS.cmd
              ] + FLAGS.app_args.split()
            flag_command = [
                 'mpirun',
                 '--allow-run-as-root',
                 '-mca','oob','tcp',
                 '-mca','pml','ob1',
                 '-mca','btl','tcp,vader,self',
                 '-n',str(podCount),
#                 '-x','MXM_IB_PORTS=mlx5_0:0',
                 '-host', hostList,
                 'touch',
                 './appflag'
              ]
        print("Running command\n")
        print(exec_command)
        print("---\n")
        resp = stream(v1.connect_get_namespaced_pod_exec, masterPod.metadata.name, masterPod.metadata.namespace,
                command=exec_command,
                    stderr=True, stdin=False,
                    stdout=True, tty=False)
        print("Response from pod %s is :%s \n" %(masterPod.metadata.name, resp))
        print("Running command\n")
        print(flag_command)
        print("---\n")
        resp = stream(v1.connect_get_namespaced_pod_exec, masterPod.metadata.name, masterPod.metadata.namespace,
                command=flag_command,
                    stderr=True, stdin=False,
                    stdout=True, tty=False)
        print("Response from pod %s is :%s \n" %(masterPod.metadata.name, resp))
    else:
        print("No master pod\n")
    print("-------------------------------------------")        
if __name__ == '__main__':
    main()
