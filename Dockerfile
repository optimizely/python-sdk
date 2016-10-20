FROM python:2.7.10

MAINTAINER Ali Rizvi <ali@optimizely.com>

# GitHub branch from which to build the SDK. Defaults to master
ARG SDK_BRANCH=master
ENV SDK_BRANCH $SDK_BRANCH

ENV INSTALL_PATH /usr/src/app
RUN mkdir -p $INSTALL_PATH
COPY . $INSTALL_PATH
WORKDIR $INSTALL_PATH
RUN pip install -r requirements.txt

EXPOSE  5000
CMD ["python", "application.py"]
