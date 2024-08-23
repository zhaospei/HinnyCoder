FROM ubuntu:22.04

MAINTAINER echodrift <luuvanducthieu291@gmail.com>

#############################################################################
# Requirements
#############################################################################

RUN apt-get update -y && apt-get install software-properties-common -y 
RUN apt-get install -y openjdk-8-jdk openjdk-17-jdk git build-essential subversion perl curl unzip cpanminus make
ENV TZ=America/Los_Angeles DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y wget checkinstall libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz && \
    tar xzf Python-3.11.8.tgz && \
    cd Python-3.11.8 && \
    ./configure --enable-optimizations && \
    make altinstall
RUN rm -rf /var/lib/apt/lists/*

#############################################################################
# Setup Defects4J
#############################################################################

# Java version
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

# Timezone
ENV TZ=America/Los_Angeles  
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# ----------- Step 1. Clone defects4j from github --------------
WORKDIR /
RUN git clone https://github.com/rjust/defects4j.git defects4j

# ----------- Step 2. Initialize Defects4J ---------------------
WORKDIR /defects4j
RUN cpanm --installdeps .
RUN ./init.sh

# ----------- Step 3. Add Defects4J's executables to PATH: ------
ENV PATH="/defects4j/framework/bin:${PATH}"
#--------------
#############################################################################
# Setup RAMBO
#############################################################################
WORKDIR /
RUN mkdir RAMBO
COPY data/adapt_defects4j.parquet RAMBO/
COPY parse_project RAMBO/
COPY processors RAMBO/
COPY make.sh RAMBO/



