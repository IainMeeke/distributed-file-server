#!/usr/bin/python


import socket
import sys
from threading import Thread
from Queue import Queue
import os

from urllib2 import urlopen

HOST = ''  # host becomes any address the machine happens to have
PORT = int(sys.argv[1])  # get the port from the command line arguments and convert to int
IP = urlopen('http://ip.42.pl/raw').read()
STUDENT_ID = '39e95f0efebef82542626bd6c3c28765726768817d45d38b2d911b26eb5d0b37'
POOL_SIZE = 20
DIRECTORY_PORT = 8888


class Worker(Thread):
    """individual thread that handles the clients requests"""

    def __init__(self, tasks, messageParser):
        Thread.__init__(self)
        self.tasks = tasks  # each task will be an individual connection
        self.messageParser = messageParser
        self.daemon = True
        self.start()

    def run(self):
        # run forever
        while True:
            conn = self.tasks.get()  # take a connection from the queue
            self.messageParser(conn)
            self.tasks.task_done()


class ThreadPool:
    """pool of worker threads all consuming tasks"""

    def __init__(self, num_thread, chat_server):
        self.tasks = Queue(num_thread)
        self.chat_server = chat_server
        for _ in range(num_thread):
            Worker(self.tasks, chat_server.messageParser)

    def add_tasks(self, conn):
        # put a new connection on the queue
        self.tasks.put((conn))


class LockServer:
    """a chat server with several chat rooms"""



    DIRECTORY_SERVER_IP = ''
    DIRECTORY_SERVER_PORT = DIRECTORY_PORT
    SERVER_ROOT = os.getcwd()
    LOCK_GRANTED = "LOCK_GRANTED\n\n"
    LOCK_FAILURE = "LOCK_FAILED\n\n"

    def __init__(self, port, num_thread):
        self.locks = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((HOST, port))
        except socket.error, msg:
            print 'binding failed, error: ' + str(msg[0])
            sys.exit()
        print 'succesful bind'
        # init a thread pool:
        self.pool = ThreadPool(num_thread, self)

    def listen(self):
        """loops for ever and puts new connections on the queue"""
        self.socket.listen(5)
        print 'listening now'
        # keep the server alive
        while True:
            connection, addr = self.socket.accept()  # blocking call to wait for a connection
            print 'connected with ' + addr[0] + ' port: ' + str(addr[1])
            self.pool.add_tasks(connection)

    def messageParser(self, conn):
        """reads a message from the connection and calls the appropriate function based on that message"""
        while conn:
            data = conn.recv(2048)
            if data == "KILL_SERVICE\n":
                os._exit(0)
            elif data.startswith("HELO") and data.endswith("\n"):
                conn.sendall('{}IP:{}\nPort:{}\nStudentID:{}\n'.format(data, IP, PORT, STUDENT_ID))
            elif data.startswith("GET_LOCK:") and data.endswith("\n"):
                self.__getLock(data, conn)
            elif data.startswith("FREE_LOCK") and data.endswith("\n"):
                self.__freeLock(data, conn)

    def __freeLock(self,data,conn):
        text = data.splitlines()
        file_id = text[0].split(":")[1]
        self.locks[file_id] = False

    def __getLock(self,data,conn):
        """checks if the requested file is locked, if so then it responds with failure message. Otherwise the lock is granted"""
        text = data.splitlines()
        file_id = text[0].split[":"][1]
        response = ''
        if file_id in self.locks and self.locks[file_id] == True:
            if self.locks[file_id] == True:
                response = self.LOCK_FAILURE
            else:
                response = self.LOCK_GRANTED
                self.locks[file_id] = True
        else:
            self.locks[file_id] = True
            response = self.LOCK_GRANTED
        conn.sendall(response)






def main():
    server = LockServer(PORT, POOL_SIZE)
    server.listen()


if __name__ == "__main__":
    main()
