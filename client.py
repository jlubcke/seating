from time import sleep
import requests


class SeatingSlave(object):
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def run(self):
        while True:
            response = requests.get('http://%s:%s/get_best_state' % (self.addr, self.port))
            print response.content
            sleep(5)
