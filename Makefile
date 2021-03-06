HERE = $(shell pwd)
BIN = $(HERE)/bin
PYTHON = $(BIN)/python

INSTALL = $(BIN)/pip install --use-mirrors
BUILD_DIRS = bin build elasticsearch include lib lib64 man share

ES = $(HERE)/elasticsearch
ES_VERSION ?= 0.20.5
ES_PATH ?= $(ES)

.PHONY: all build clean test

all: build

$(PYTHON):
	virtualenv --distribute .

build: $(PYTHON) elasticsearch
	$(PYTHON) setup.py develop
	$(INSTALL) pyelastictest[test]

clean:
	rm -rf $(BUILD_DIRS)

test:
	ES_PATH=$(ES_PATH) \
	$(BIN)/nosetests -d -s -v --with-coverage --cover-package pyelastictest pyelastictest

html:
	cd docs && \
	make html

elasticsearch:
	curl -C - http://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-$(ES_VERSION).tar.gz | tar -zx
	mv elasticsearch-$(ES_VERSION) elasticsearch
	chmod a+x elasticsearch/bin/elasticsearch
	mv elasticsearch/config/elasticsearch.yml elasticsearch/config/elasticsearch.in.yml
	cp elasticsearch.yml elasticsearch/config/elasticsearch.yml
