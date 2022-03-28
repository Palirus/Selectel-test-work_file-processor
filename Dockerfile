FROM python:3.9-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update ; \
    apt-get install -y \
        tzdata \
        gcc \
        postgresql-server-dev-all \
        python3-dev \
        musl-dev \
        libffi-dev \
        make \
        openssh-server \
        openssh-client \
        vim \
    && ln -nfs /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
    && echo Europe/Moscow > /etc/timezone \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && rm requirements.txt

RUN mkdir /var/run/sshd && \
chmod 0755 /var/run/sshd

RUN useradd -m -d /home/test -s /bin/bash -g root -G sudo -u 1001 test
RUN echo "test:test" | chpasswd

EXPOSE 22

CMD service ssh start && sleep infinity

# RUN mkdir /var/run/sshd
# RUN echo 'root:pass' | chpasswd
# RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
# EXPOSE 22

# RUN apt-get update
# RUN apt-get upgrade
# RUN apt install -y  \
#                 openssh-client \
#                 openssh-server \
#                 htop \
#                 psmisc \
#                 net-tools

     
# Add Tini
# RUN apt-get install tini
# ENTRYPOINT ["/usr/bin/tini", "--"]

# RUN echo "root:root" | chpasswd

# CMD [ "/bin/bash" ]

# EXPOSE 22
