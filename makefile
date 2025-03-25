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

