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
    && pip install -r requirements.txt 

RUN mkdir /var/run/sshd && \
chmod 0755 /var/run/sshd

RUN useradd -m -d /home/test -s /bin/bash -g root -G sudo -u 1001 test
RUN echo "test:test" | chpasswd

EXPOSE 22
