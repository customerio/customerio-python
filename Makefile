PYTHON ?= python3

all:
	$(PYTHON) setup.py sdist
	$(PYTHON) -m doctest ./customerio/__init__.py

install:
	$(PYTHON) setup.py install

clean:
	$(PYTHON) setup.py clean
	rm -rf MANIFEST build dist

dev: clean all
	if ! pip uninstall customerio; then echo "customerio not installed, installing it for the first time" ; fi
	pip install dist/*
	$(PYTHON) -i -c "from customerio import *"

upload:
	$(PYTHON) setup.py register
	echo "*** Now upload the binary to PyPi *** (one second)" && sleep 3 && open dist & open "http://pypi.python.org/pypi?%3Aaction=pkg_edit&name=customerio" # python setup.py upload

test:
	openssl req -new -newkey rsa:2048 -days 10 -nodes -x509 -subj "/C=CA/ST=Ontario/L=Toronto/O=Test/CN=127.0.0.1" -keyout ./tests/server.pem -out ./tests/server.pem
	$(PYTHON) -m unittest discover -v
