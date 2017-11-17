all: README.rst install 

test: 
	pytest-3

install: test
	pip install -e . 

README.rst: readme.md
	pandoc --from=markdown --to=rst --output=README.rst readme.md 

.PHONY: all install test
