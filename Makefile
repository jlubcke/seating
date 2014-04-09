PYTHON = ./env/bin/python
PIP = ./env/bin/pip

all: ./env/bin/python test

$(PYTHON):
	virtualenv --no-site-packages env
	$(PIP) install numpy
	$(PIP) install bunch
	$(PIP) install xlutils
	$(PIP) install requests
	$(PIP) install pytest
	$(PIP) install simplejson

test:
	env/bin/py.test tests.py

master:
	$(PYTHON) distributed_seating.py --addr 127.0.0.1 --port 5000

slave:
	$(PYTHON) distributed_seating.py --addr 127.0.0.1 --port 5000 --slave

clean:
	rm -rf env
	find . -name "*.pyc" -exec rm {} \;
