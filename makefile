# Variables
CONFIG_DIR := ./config
GCS_BUCKET := gs://wfcrai-agents/config/

# Find all .toml files in the config directory
TOML_FILES := $(shell find $(abspath $(CONFIG_DIR)) -name '*.toml' ! -name 'bundled.toml')

# Default target
.PHONY: push_config
push_config: $(TOML_FILES)
	@echo "Pushing TOML files to GCS using rsync..."
	@gsutil -m rsync -r $(CONFIG_DIR) $(GCS_BUCKET)
	@echo "Done pushing TOML files."

.PHONY: bundle 
bundle: $(TOML_FILES)
	rm -f $(CONFIG_DIR)/bundled.toml
	@echo "Creating bundled.toml by concatenating all TOML files..."
	@echo "Bundling the following TOML files:"
	@echo $(TOML_FILES) | tr ' ' '\n'
	@cat $(TOML_FILES) > $(CONFIG_DIR)/bundled.toml