
all:
	python setup.py sdist
	python -m doctest ./customerio/__init__.py

install:
	python setup.py install

clean:
	python setup.py clean
	rm -rf MANIFEST build dist

dev: clean all
	if ! pip uninstall customerio; then echo "customerio not installed, installing it for the first time" ; fi
	pip install dist/*
	python -i -c "from customerio import *"

upload:
	python setup.py register
	echo "*** Now upload the binary to PyPi *** (one second)" && sleep 3 && open dist & open "http://pypi.python.org/pypi?%3Aaction=pkg_edit&name=customerio" # python setup.py upload

test:
	openssl req -new -newkey rsa:1024 -days 10 -nodes -x509 -subj "/C=CA/ST=Ontario/L=Toronto/O=Test/CN=127.0.0.1" -keyout ./tests/server.pem -out ./tests/server.pem
	python -m unittest discover -v
