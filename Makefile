PYTHON ?= python3
OPENSSL ?= openssl
SERVER_CERT := tests/server.pem

all: build
	$(PYTHON) -m doctest ./customerio/__init__.py

install:
	$(PYTHON) -m pip install .

clean:
	rm -rf MANIFEST build dist customerio.egg-info .ruff_cache

dev: clean all
	if ! pip uninstall customerio; then echo "customerio not installed, installing it for the first time" ; fi
	pip install dist/*
	$(PYTHON) -i -c "from customerio import *"

upload:
	$(PYTHON) -m twine upload dist/*

build:
	$(PYTHON) -m build

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

test: $(SERVER_CERT)
	$(PYTHON) -m unittest discover -v

$(SERVER_CERT):
	$(OPENSSL) req -new -newkey rsa:2048 -days 10 -nodes -x509 -subj "/C=CA/ST=Ontario/L=Toronto/O=Test/CN=127.0.0.1" -keyout $(SERVER_CERT) -out $(SERVER_CERT)
