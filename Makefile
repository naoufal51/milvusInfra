SHELL := /bin/bash

STACK_NAME=dev
PULUMI_CMD=pulumi --non-interactive --stack $(STACK_NAME)


install-deps:
	curl -fsSL https://get.pulumi.com | sh
	pip3 install -r infra/requirements.txt

deploy:
	$(PULUMI_CMD) stack init $(STACK_NAME) || true
	$(PULUMI_CMD) config set aws:region $(AWS_REGION)
	$(PULUMI_CMD) config set baseStackName $(BASE_STACK_NAME)
	$(PULUMI_CMD) preview
#	$(PULUMI_CMD) up --yes