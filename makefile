# Variables
CONFIG_DIR := ./config
GCS_BUCKET := gs://wfcrai-agents/data-agent

# Find all prompt .toml files in the config directory
TOML_FILES := $(shell find $(CONFIG_DIR)/prompts -name '*.toml' ! -name 'bundled.toml')

# Default target
.PHONY: push_config
push_config: bundle
	@echo "Pushing bundled.toml to GCS..."
	@gsutil cp $(CONFIG_DIR)/bundled.toml $(GCS_BUCKET)/config/bundled.toml
	@echo "Done pushing bundled.toml."

.PHONY: bundle 
bundle: $(TOML_FILES)
	rm -f $(CONFIG_DIR)/bundled.toml
	@echo "Creating bundled.toml by concatenating shared.toml and all TOML files..."
	@echo "Bundling the following TOML files:"
	@echo $(CONFIG_DIR)/shared.toml $(TOML_FILES) | tr ' ' '\n'
	@cat $(CONFIG_DIR)/shared.toml $(TOML_FILES) > $(CONFIG_DIR)/bundled.toml

.PHONY: utils
utils:
	@echo "Building agent_utils..."
	@cd ../agent_utils && uv build
	@echo "Copying the built .whl file from agent_utils..."
	@cp ../agent_utils/dist/*.whl .
	@echo "Installing agent_utils into the current project..."
	@uv pip install *.whl
	@echo "Done adding and installing agent_utils."

.PHONY: push # Push to artifact registry
push: push 
	@echo "Building docker image locally as data-agent:latest..."
	@docker build . -t data-agent:latest
	@docker tag data-agent:latest us-central1-docker.pkg.dev/gcp-wow-food-fco-auto-dev/gae-standard/data-agent:latest
	@echo "Pushing the Docker image to Artifact Registry..."
	@docker push us-central1-docker.pkg.dev/gcp-wow-food-fco-auto-dev/gae-standard/data-agent:latest

.PHONY: build # Build the docker image
build: build
	@echo "Building docker image locally as data-agent:latest..."
	@docker build . -t data-agent:latest
	@docker tag data-agent:latest us-central1-docker.pkg.dev/gcp-wow-food-fco-auto-dev/gae-standard/data-agent:latest