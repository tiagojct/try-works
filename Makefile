.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

generate: ## Regenerate CSS variables and Tailwind colours from try-works.json
	python3 scripts/generate.py

css: generate ## Alias for generate

tailwind: generate ## Alias for generate

demo: ## Compile the Typst demo deck (needs typst + the three fonts)
	typst compile typst/demo.typ demo.pdf

clean: ## Remove build artefacts
	rm -rf web/_site demo.pdf

.PHONY: help generate css tailwind demo clean

cvd: ## Run the colour-vision-deficiency check
	python3 scripts/cvd_check.py
.PHONY: cvd

validate: ## Validate tokens, hex, mode parity, and WCAG contrast
	python3 scripts/validate.py

check: ## Verify generated files match the json (the CI drift gate)
	python3 scripts/generate.py --check

test: validate check ## Run validation and the drift check
all: generate ## Regenerate every surface
.PHONY: validate check test all

fonts-check: ## Verify Portuguese coverage and subset range (needs fonts present)
	python3 scripts/check_fonts.py
.PHONY: fonts-check

fonts: ## Subset fonts to woff2 (needs source TTFs in fonts/ and brotli)
	sh scripts/subset_fonts.sh
.PHONY: fonts

dist: ## Assemble publishable copies of each surface under dist/
	sh scripts/dist.sh
.PHONY: dist
