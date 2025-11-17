#!/usr/bin/make

ifneq ($(if $(MAKECMDGOALS),$(words $(MAKECMDGOALS)),1),1)
.SUFFIXES:
TARGET := $(if $(findstring :,$(firstword $(MAKECMDGOALS))),,$(firstword $(MAKECMDGOALS)))
PARAMS := $(if $(findstring :,$(firstword $(MAKECMDGOALS))),$(MAKECMDGOALS),$(wordlist 2,100000,$(MAKECMDGOALS)))
.DEFAULT_GOAL = help
.PHONY: ONLY_ONCE
ONLY_ONCE:
	$(MAKE) $(TARGET) COMMAND_ARGS="$(PARAMS)"
%: ONLY_ONCE
	@:
else

help: ## Help
	@grep -E '(^[a-zA-Z0-9_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}{printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'

SHELL = /bin/bash
ifeq ($(filter help, $(MAKECMDGOALS)),)
-include .env
export $(shell sed '/^#/d; s/=.*//' .env)
endif

mongo: ## Run MongoDB in Docker
	docker run -d \
	--name mongodb \
	-p 27017:27017 \
	-v mongo_data:/data/db \
	-e MONGO_INITDB_ROOT_USERNAME=root \
	-e MONGO_INITDB_ROOT_PASSWORD=example \
	mongo



endif