EXAMPLES ?= .
VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip
REQUIREMENTS = requirements.txt

.PHONY: venv install test clean

venv: $(VENV_NAME)/bin/activate

$(VENV_NAME)/bin/activate:
	python3 -m venv $(VENV_NAME)

install: venv
	$(PIP) install -r $(REQUIREMENTS)

run_imperative_eg: install
	$(PYTHON) $(EXAMPLES)/imperative.py

run_lg_eg_pyd: install
	$(PYTHON) langgraph/langgraph_pydantic.py

run_lg_eg_td: install
	$(PYTHON) langgraph/langgraph_typedict.py

run_llma_idx: install
	$(PYTHON) llamaindex/llamaindex_workflow.py

run_acp: install
	$(PYTHON) acp/__main__.py



clean:
	rm -rf $(VENV_NAME)
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {}
