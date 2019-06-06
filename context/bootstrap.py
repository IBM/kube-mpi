#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 # Copyright © 2018 IBM Corporation
 #
 # Licensed under the Apache License, Version 2.0 (the "License");
 # you may not use this file except in compliance with the License.
 # You may obtain a copy of the License at
 #
 #    http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS,
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 # See the License for the specific language governing permissions and
 # limitations under the License.
'''
from __future__ import print_function
from collections import OrderedDict
from kubernetes import client,config
from kubernetes.client.models.v1_pod_spec import V1PodSpec
import os
import json
import time
import subprocess
import sys
import gflags
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

FLAGS = gflags.FLAGS

gflags.DEFINE_string('cmd', '/pi 0.001', 'cmd to start the mpi job')
gflags.DEFINE_string('job_name', 'job', 'name of the job')
gflags.DEFINE_string('network', '10.1.0.0/16', 'network to run job on')

config.load_incluster_config()
v1 = client.CoreV1Api()
v1batch=client.BatchV1Api()

namespace = os.environ.get('NAMESPACE', '')
localIp   = os.environ.get('POD_IP',    '')
podName   = os.environ.get('POD_NAME',  '')

cmd = ""

def innet(ip, net):
    print(("ip: "+ip, "net: " + net))
    ip = IPAddress(ip).value
    print("ipnew: " + str(ip))
    network = IPNetwork(net)
    print("network-first: " + str(network.first))
    print("network-last: " + str(network.last))

    if ip >= network.first and ip <= network.last:
        return True
    else:
        return False

def getIp(ip):
    print ("ip:" + ip)
    host = "root@" + ip
    print("host: " + host)
    res = subprocess.Popen(["ssh", host,
                           "ip addr show | grep -Po 'inet \K[\d.]+'"],
                           stdout=subprocess.PIPE).communicate()[0]
    data = res.split()
    return data

def getPodIpStr():
    hostStr = "-host "

    isMaster = False
    ps_pods = v1.list_namespaced_pod(namespace, label_selector="job=" +
                                     FLAGS.job_name)
    job = v1batch.list_namespaced_job(namespace, label_selector="job=" +
                                      FLAGS.job_name)
    worker_num = job.items[0].spec.parallelism
    items = ps_pods.items

    print(("items=  ", len(items)))
    print("worker_num=  " + str(worker_num))

    if (len(items) < worker_num):
        return False, "", False

    for i in range(0, len(items)):
        try:
            podIp = items[i].status.pod_ip
            print("podIp:" + podIp)
            print("localIp:" + localIp)
            if (i == 0 and podIp == localIp):
                isMaster = True
            hostStr = hostStr + podIp
            if (i < len(items)-1):
                hostStr = hostStr + ","
        except Exception as err:
            return False, "", isMaster
    return True, hostStr, isMaster

# ------------------------------------------------------------------------------

def getHostIpStr():

    hostlist = []
    hostIPs = ""
    podIp = ""

    ready    = True     # ready to start mpi
    isMaster = False    # is root

    # get pods, job, and expected number of workers
    pods    = v1.list_namespaced_pod(namespace, label_selector="job="  + FLAGS.job_name).items
    job     = v1batch.list_namespaced_job(namespace, label_selector="job=" + FLAGS.job_name).items[0]
    workers = job.spec.parallelism

    containers = pods[0].spec.containers
    for container in containers :
        print(container.name)

    for i in range(len(pods)):

        # add a basic pod name based filter        
        pod_name = pods[i].metadata.name
        job_name = job.metadata.name
        if not pod_name.startswith(job_name):
            print('ignored pod "%s"' % (pod_name))
            continue

        # if number of active pods < total, job is not ready
        if job.status.active < workers:
            print('only %d out of %d pods are ready; wait' % (\
                    job.status.active, 
                    workers))
            ready = False
            break

        podIp = pods[i].status.pod_ip
        print('add pod "%s" (pod_ip="%s" local_ip="%s")' % (\
                pod_name, 
                podIp, 
                localIp))

        if (i == 0 and podName == pods[i].metadata.name):
            isMaster = True
        hostlist.append(pod_name)

    return ready, hostlist, isMaster

# ------------------------------------------------------------------------------

def startSSH():
    cmd = "systemctl start sshd"
    print (cmd)
    subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    while subp.poll() is None:
        print(subp.stdout.readline())

def execCommandhost(hostStr, items):
    #cmd = "mpirun --allow-run-as-root -mca plm_rsh_agent kssh -mca oob tcp -mca pml ob1  -mca btl_tcp_if_include %s  -n %s %s %s" % (FLAGS.network, str(len(items)), hostStr, FLAGS.cmd)
    
    cmd = "mpirun --allow-run-as-root -mca plm_rsh_agent kssh -mca btl_tcp_if_include %s --map-by core -np %d %s %s" % (\
            FLAGS.network,
            len(items), 
            hostStr, 
            FLAGS.cmd)
    print('Command:', cmd)
    subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    while subp.poll() is None:
        print(subp.stdout.readline())
    print(subp.returncode)

def execCommandpod(hostStr):
    cmd = "mpirun --allow-run-as-root -mca oob tcp -mca pml ob1 -mca btl tcp,vader,self -n 2 %s %s" % (\
            hostStr, 
            FLAGS.cmd)
    print(cmd)
    subp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    while subp.poll() is None:
        print(subp.stdout.readline())
    print(subp.returncode)

def waitOrExit():
    while True:
        time.sleep(3)
        ps_pods = v1.list_namespaced_pod(namespace, label_selector="job=" + FLAGS.job_name)
        items = ps_pods.items
        if (items[0].status.phase != "Running"):
            print("job finished, exit...")
            return

if __name__ == "__main__":

    host_network = False
    isParamReady = False
    hostStr = ""
    isMaster = False

    FLAGS(sys.argv)
    startSSH()

    print ("service sshd finished")
    print ("FLAGS.job_name: " + FLAGS.job_name)

    # --------------------------------------------------------------------------

    print()
    print(80 * '-')
    print(80 * '-')
    os.system('env')
    print(80 * '-')

    podlist = v1.list_namespaced_pod(namespace, label_selector="job=" + FLAGS.job_name)
    pods    = podlist.items

    for pod in pods:
        print('pod host_ip=%s pod_ip=%s name=%s' % (\
                pod.status.host_ip, 
                pod.status.pod_ip, 
                pod.metadata.name))
    print(80 * '-')
    print()

    # --------------------------------------------------------------------------

    ps_pods = v1.list_namespaced_pod(namespace, include_uninitialized=False, 
                                     label_selector="job="
                                     + FLAGS.job_name)
    items = ps_pods.items
    print ("len of items: " + str(len(items)))
    
    for item in items:
        host_network = item.spec.host_network
        print ("host_network: " + str(host_network))

    while not isParamReady: 
        if not host_network:
            isParamReady, hostStr, isMaster = getPodIpStr()
        else:
            isParamReady, hostlist, isMaster = getHostIpStr()
        time.sleep(1)

    if   isParamReady and isMaster and not host_network:
        execCommandpod(hostStr)
    elif isParamReady and isMaster and host_network:
        hostStr = '-host ' + ','.join(sorted(20*hostlist))
        execCommandhost(hostStr, items)
    else:
        waitOrExit()

