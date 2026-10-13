PYTHON = python3

.PHONY: run test

run:
	$(PYTHON) src/main.py $(ARGS)

test:
	$(PYTHON) -m unittest discover -s tests -v
