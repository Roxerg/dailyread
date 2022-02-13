#!/bin/bash
app="docker.test"
docker build -t ${app} .
docker run -p 56733:8000 \
  --name=${app} \
  -v $PWD:/app ${app}
