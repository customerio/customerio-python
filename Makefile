
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
	python setup.py upload
