python distributed_seating.py --addr 127.0.0.1 --port 5000
python distributed_seating.py --addr 127.0.0.1 --port 5000 --slave
for x in {0..7}; do (python distributed_seating.py --addr 127.0.0.1 --port 5000 --slave &); done

virtualenv env
. env/bin/activate

# numpy stuff

pip install numpy
pip install bunch
pip install requests
pip install pytest

# Extra

brew import pyqt
pip install ipython
brew install pkg-config
brew install freetype
ln -s /usr/local/opt/freetype/include/freetype2 /usr/local/include/freetype
pip install matplotlib
pip install pyzmq
pip install jinja2
pip install tornado
