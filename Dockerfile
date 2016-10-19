FROM ruby:2.3.1

MAINTAINER Ali Rizvi <ali@optimizely.com>

# GitHub branch from which to build the SDK. Defaults to master
ARG SDK_BRANCH=master
ENV SDK_BRANCH $SDK_BRANCH

RUN mkdir -p /usr/src/app
COPY . /usr/src/app
WORKDIR /usr/src/app
RUN bundle install

EXPOSE 3000
CMD ["bundle", "exec", "ruby", "./main.rb"]
