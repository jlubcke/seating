all: virtual_env test

virtual_env:
	virtualenv --no-site-packages env
	env/bin/pip install numpy 
	env/bin/pip install bunch 
	env/bin/pip install xlutils
	env/bin/pip install requests 
	env/bin/pip install pytest 
	env/bin/pip install simplejson

test:
	env/bin/py.test tests.py

master:
	env/bin/python distributed_seating.py --addr 127.0.0.1 --port 5000

slave:
	env/bin/python distributed_seating.py --addr 127.0.0.1 --port 5000 --slave

clean:
	rm -rf env
	find . -name "*.pyc" -exec rm {} \;
