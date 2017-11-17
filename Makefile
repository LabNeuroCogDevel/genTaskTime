all: install README.rst

install:
	pip install -e . 

README.rst: readme.md
	pandoc --from=markdown --to=rst --output=README.rst readme.md 

.PHONY: all install
