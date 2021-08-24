FROM centos:8

ENV MOFED_VERSION 5.0-1.0.0.0
ENV OS_VERSION rhel8.2
ENV PLATFORM x86_64
ENV MOFED_DIR MLNX_OFED_LINUX-${MOFED_VERSION}-${OS_VERSION}-${PLATFORM}
ENV OMPI_VERSION v4.0.2
ENV K8SVERSION v1.21.0

WORKDIR /
RUN  yum -y update && yum clean all &&          \
     yum -y  install                            \
                        epel-release            \
                        lsb                     \
                        wget                    \
                        gcc gcc-c++ make        \
                        gcc-gfortran            \
			numactl-libs		\
			libnl3			\
			libmnl			\
			tcl			\
			tcsh			\
			tk			\
			git			\
			autoconf		\
			libtool			\
			flex			\
			numactl-devel		\
                        binutils-devel 		\
                        systemd-libs 		\
			tar		 	\
			openssh-server	 	\
                         && yum clean all

RUN ln -s /usr/lib64/libudev.so.1 /usr/lib64/libudev.so
WORKDIR /
ENV TERM vt100
ENV LANG=en_US.utf-8

# adding support for Mellanox IB
RUN yum -y install lsof pciutils
RUN wget http://content.mellanox.com/ofed/MLNX_OFED-${MOFED_VERSION}/MLNX_OFED_LINUX-${MOFED_VERSION}-${OS_VERSION}-${PLATFORM}.tgz && \
    tar -xvf MLNX_OFED_LINUX-${MOFED_VERSION}-${OS_VERSION}-${PLATFORM}.tgz && \
    MLNX_OFED_LINUX-${MOFED_VERSION}-${OS_VERSION}-${PLATFORM}/mlnxofedinstall --distro ${OS_VERSION} --with-nvmf  --user-space-only --without-fw-update -q && \
    cd .. && \
    rm -rf ${MOFED_DIR} && \
    rm -rf *.tgz

#configure and build pmix,openmpi
ARG CC=gcc
ARG CFLAGS="-g -O2  -I/usr/local/include"
ARG FC=gfortran
ARG FCFLAGS="-g -O2 "
ARG LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:/usr/lib64
##
###download and build openmpi
#WORKDIR /
RUN wget https://download.open-mpi.org/release/open-mpi/v4.0/openmpi-4.0.2.tar.gz && \
tar -xvf openmpi-4.0.2.tar.gz 
WORKDIR openmpi-4.0.2
RUN ./configure --enable-shared --enable-mca-no-build=btl-uct --disable-static  --enable-mpi-fortran=usempi  --disable-libompitrace --enable-script-wrapper-compilers --enable-wrapper-rpath --with-hcoll=/opt/mellanox/hcoll --with-ucx=/usr --with-ucx-libdir=/usr/lib64/  &&  make && make install
RUN rm -rf openmpi-4.0.2
## get kubectl

RUN curl -LO https://dl.k8s.io/release/${K8SVERSION}/bin/linux/amd64/kubectl 
RUN cp kubectl /usr/local/bin
RUN chmod +x /usr/local/bin/kubectl
##
COPY wait4app.sh /
COPY launcher.sh /
COPY launcherz.sh /
COPY kssh /
##
ENV PATH /usr/local/bin:./:/:$PATH
ENV LD_LIBRARY_PATH /usr/local/lib:/opt/mellanox/mxm:/opt/mellanox/hcoll:$LD_LIBRARY_PATH
###
ENTRYPOINT ["./wait4app.sh"]
##CMD ["bash"]
