.PHONY: help clean build test upload upload-test install check version

# Default target
help:
	@echo "Available targets:"
	@echo "  make install     - Install development dependencies"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make build       - Build distribution packages"
	@echo "  make test        - Run tests"
	@echo "  make check       - Check package before building"
	@echo "  make upload-test - Upload to TestPyPI"
	@echo "  make upload      - Upload to PyPI"
	@echo "  make version     - Show current version"

# Variables
PYTHON := python3
PACKAGE_NAME := lunacept
VERSION := $(shell grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Install development dependencies
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned build artifacts"

# Check package before building
check:
	@echo "Checking package configuration..."
	$(PYTHON) -m pip install --upgrade build twine
	$(PYTHON) -m build --check
	@echo "Package check passed"

# Build distribution packages
build: clean
	@echo "Building version $(VERSION)..."
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "Build complete. Distribution files in dist/"

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Show current version
version:
	@echo "Current version: $(VERSION)"

# Upload to TestPyPI
upload-test: build
	@echo "Uploading $(VERSION) to TestPyPI..."
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "Uploaded to TestPyPI. Test with: pip install -i https://test.pypi.org/simple/ $(PACKAGE_NAME)==$(VERSION)"

# Upload to PyPI
upload: build
	@echo "Uploading $(VERSION) to PyPI..."
	@read -p "Are you sure you want to upload to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -m pip install --upgrade twine; \
		$(PYTHON) -m twine upload dist/*; \
		echo "Uploaded to PyPI"; \
	else \
		echo "Upload cancelled"; \
	fi

# Full release workflow (build + upload)
release: clean build upload

# Test release workflow (build + upload to testpypi)
release-test: clean build upload-test

