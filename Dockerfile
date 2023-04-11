FROM ubuntu:18.04

ENV RUNNER_VERSION=2.291.1

RUN useradd -m actions
RUN apt-get -yqq update && apt-get install -yqq curl jq wget

RUN \
  latest_version_label="$(curl -s -X GET 'https://api.github.com/repos/actions/runner/releases/latest' | jq -r '.tag_name')" \
  RUNNER_VERSION="$(echo ${latest_version_label:1})" \
  cd /home/actions && mkdir actions-runner && cd actions-runner \
    && wget https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && rm actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz


WORKDIR /home/actions/actions-runner
RUN chown -R actions ~actions && /home/actions/actions-runner/bin/installdependencies.sh

RUN apt-get install -yqq python3 python3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

USER actions
COPY main.py main.py
COPY logger.cfg logger.cfg
CMD ["python3", "main.py"]
