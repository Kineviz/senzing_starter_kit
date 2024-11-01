# Makefile extensions for windows.

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

SENZING_TOOLS_DATABASE_URL ?= sqlite3://na:na@nowhere/C:\Temp\sqlite\G2C.db

# -----------------------------------------------------------------------------
# OS specific targets
# -----------------------------------------------------------------------------

.PHONY: clean-osarch-specific
clean-osarch-specific:
	@docker rm  --force $(DOCKER_CONTAINER_NAME)
	@docker rmi --force $(DOCKER_IMAGE_NAME) $(DOCKER_BUILD_IMAGE_NAME)
	del /F /S /Q $(DIST_DIRECTORY)
	del /F /S /Q $(MAKEFILE_DIRECTORY)/.coverage
	del /F /S /Q $(MAKEFILE_DIRECTORY)/.mypy_cache
	del /F /S /Q $(MAKEFILE_DIRECTORY)/.pytest_cache
	del /F /S /Q $(MAKEFILE_DIRECTORY)/__pycache__
	del /F /S /Q $(MAKEFILE_DIRECTORY)/coverage.xml
	del /F /S /Q $(MAKEFILE_DIRECTORY)/dist
	del /F /S /Q $(MAKEFILE_DIRECTORY)/docs/build
	del /F /S /Q $(MAKEFILE_DIRECTORY)/htmlcov
	del /F /S /Q $(TARGET_DIRECTORY)


.PHONY: coverage-osarch-specific
coverage-osarch-specific: export SENZING_LOG_LEVEL=TRACE
coverage-osarch-specific:
	@pytest --cov=src --cov-report=xml  $(shell git ls-files '*.py')
	@coverage html
	@explorer $(MAKEFILE_DIRECTORY)/htmlcov/index.html


.PHONY: docker-build-osarch-specific
docker-build-osarch-specific:
	@docker build \
		--tag $(DOCKER_IMAGE_NAME) \
		--tag $(DOCKER_IMAGE_NAME):$(BUILD_VERSION) \
		.


.PHONY: documentation-osarch-specific
documentation-osarch-specific:
	# @cd docs; rm -rf build; make html
	@explorer file://$(MAKEFILE_DIRECTORY)/docs/build/html/index.html


.PHONY: hello-world-osarch-specific
hello-world-osarch-specific:
	$(info Hello World, from windows.)


.PHONY: package-osarch-specific
package-osarch-specific:
	# cp  $(MAKEFILE_DIRECTORY)/template-python.py $(MAKEFILE_DIRECTORY)/src/template_python/main_entry.py
	@python3 -m build
	# rm $(MAKEFILE_DIRECTORY)/src/template_python/main_entry.py


.PHONY: setup-osarch-specific
setup-osarch-specific:
	$(info No setup required.)


.PHONY: test-osarch-specific
test-osarch-specific:
	@$(activate-venv); pytest


.PHONY: venv-osarch-specific
venv-osarch-specific:
	@python -m venv .venv

# -----------------------------------------------------------------------------
# Makefile targets supported only by this platform.
# -----------------------------------------------------------------------------

.PHONY: only-windows
only-windows:
	$(info Only windows has this Makefile target.)
