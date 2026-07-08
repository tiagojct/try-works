.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

generate: ## Regenerate every surface from src/try-works.json into dist/
	python3 src/scripts/generate.py
	sh src/scripts/assemble.sh

css: generate ## Alias for generate

tailwind: generate ## Alias for generate

dist: generate ## Alias for generate (dist/ is the build output)

demo: ## Compile the Typst demo deck (needs typst + the three fonts)
	typst compile src/typst/demo.typ demo.pdf

clean: ## Remove transient build artefacts (keeps committed dist/)
	rm -rf src/web/_site demo.pdf

.PHONY: help generate css tailwind dist demo clean

cvd: ## Run the colour-vision-deficiency check
	python3 src/scripts/cvd_check.py
.PHONY: cvd

validate: ## Validate tokens, hex, mode parity, and WCAG contrast
	python3 src/scripts/validate.py

check: ## Verify generated files match the json (the CI drift gate)
	python3 src/scripts/generate.py --check

test: validate check ## Run validation and the drift check
all: generate ## Regenerate every surface
.PHONY: validate check test all

fonts-check: ## Verify Portuguese coverage and subset range (needs fonts present)
	python3 src/scripts/check_fonts.py
.PHONY: fonts-check

fonts: ## Subset fonts to woff2 (needs source TTFs in src/fonts/ and brotli)
	sh src/scripts/subset_fonts.sh
.PHONY: fonts
