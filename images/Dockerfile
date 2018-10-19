 #
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
 #

FROM ppc64le/centos

WORKDIR /
RUN  yum -y update && yum clean all &&          \
     yum -y  install                            \
	                epel-release            \
    		        lsb                 	\
                        wget                    \
                        gcc gcc-c++ make        \
                        gcc-gfortran           	\
                        binutils-devel        	\
                        openssh-server      	\
                        vim                 	\
                        libtcl*                 \
			libnl-route-*           \
                        libcrypto*          	\
                        libssl*             	\
                        libnuma*            	\
                        libevent*            	\
                        dkms*                	\
                        openssl             	\
                        git                 	\
                        libtool                	\
                        pciutils            	\
                        module-init-tools   	\
                        kmod                	\
			libmnl                  \
			tcsh                    \
                        lsof                	\
                        curl*               	\
                        numa*               	\
                        gnu*                    \
                        autoconf               	\
                        flex                    \
                        zlib*                   \
			hwloc                   \
			hwloc-devel


RUN   yum -y  install                           \
                        python-pip*             \
                        python-gflags*          \
                        python-devel*           \
                        python-netifaces        \
                        python-netaddr          \
                        python-setuptools-*     \
                        python-cryptography     \
                        python-libxml2*


RUN yum -y install  czmq-*

# adding support for kubernetes API access from docker
#RUN pip install --upgrade pip --ignore-installed
RUN pip install kubernetes --disable-pip-version-check
#RUN pip install kubernetes --ignore-installed


WORKDIR /
# adding support for Mellanox IB
#ENV TERM vt100
#COPY  MLNX_OFED_LINUX-4.4-1.0.0.0-rhel7.5-ppc64le-ext /
#RUN ./mlnxofedinstall --user-space-only --without-fw-update	--all --force -q

#configure and build pmix,openmpi
ARG CC=gcc
ARG CFLAGS="-g -O2 -mcpu=power8 -I/usr/local/include"
ARG FC=gfortran
ARG FCFLAGS="-g -O2 -mcpu=power8"
ARG LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:/usr/lib64

#download and build PMIx
WORKDIR /
RUN git clone https://github.com/pmix/pmix.git
RUN cd pmix && git checkout remotes/origin/v2.1 && ./autogen.pl && \
./configure --with-libevent-libdir=/usr/lib64 --with-libevent-header=/usr/include/event.h &&  make && make install

#download and build openmpi 
WORKDIR /
RUN git clone https://github.com/open-mpi/ompi.git
RUN cd ompi && git checkout remotes/origin/v3.0.x && ./autogen.pl && \
./configure --with-flux --with-hwloc=external --with-libevent=/usr --with-pmix=/usr/local/ --with-pmix-libdir=/usr/local/lib  --enable-shared --disable-static  --enable-mpi-fortran=usempi  --disable-libompitrace --enable-script-wrapper-compilers --enable-wrapper-rpath  &&  make && make install

# set ld path and ssh key
RUN echo "/usr/local/lib" >> /etc/ld.so.conf && ldconfig
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

WORKDIR /
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/ppc64le/kubectl
RUN chmod +x kubectl
COPY bootstrap.py /usr/local/bin/
RUN chmod +x /usr/local/bin/bootstrap.py
COPY kssh /
RUN chmod +x kssh
ENV PATH /usr/local/bin:./:/:$PATH
# if using mellanox accelerator libraries for collectives
#ENV LD_LIBRARY_PATH /usr/local/lib:/opt/mellanox/mxm:/opt/mellanox/hcoll:$LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH
ADD example example
WORKDIR /example/
RUN  mpicc hello.c -o hello
RUN cp  hello /
WORKDIR /
ENTRYPOINT /bin/bash
