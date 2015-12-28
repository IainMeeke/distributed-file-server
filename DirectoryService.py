import hashlib
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



class DirectoryServer:
    """a chat server with several chat rooms"""

    FILE_LOCATION_RESPONSE = "SERVER IP:{0}\nSERVER PORT:{1}\nFILE ID:{2}\n\n"
    ADD_FILE_SUCCESS_RESPONSE = "FILE ADDED\n\n"
    FAILURE_RESPONSE = "ERROR:{0}\n\n"
    SERVER_ROOT = os.getcwd()

    def __init__(self, port, num_thread):
        self.file_locations = {"hello.txt":[HOST,443,"1.txt"]} #dictionary for all files = {file_path:[server ip, server port, file_id], file_name.....}
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
            elif data.startswith("GET FILE") and data.endswith("\n"):
                self.getFileLocation(conn,data)

    def getFileLocation(self,conn,data):
        """given a file path it wil return the server ip, port and the file id on the server
        data should be in the form GET FILE:[file_path]\n\n"""
        file_path = data.split(":")[1].strip()
        response = ""
        if file_path in self.file_locations:
            file_location_data = self.file_locations[file_path]
            server_ip = file_location_data[0]
            server_port = file_location_data[1]
            file_id = file_location_data[2]
            response += self.FILE_LOCATION_RESPONSE.format(server_ip,server_port,file_id)
        else:
            response += self.FAILURE_RESPONSE.format("file not found")
        conn.sendall(response)

    def addFileLocation(self,conn,data):
        """given a file path and server details it adds it adds it to self.file_locations
        data should be of the form FILE PATH :[file_path]\nSERVER IP:[server_ip]\nSERVER PORT:[Server_port]\nFILE ID:[file_id]\n\n"""
        text = data.splitlines()
        file_path = text[0].split(":")[1]
        server_ip = text[1].split(":")[1]
        server_port = text[2].split(":")[1]
        file_id = text[3].split(":")[1]
        response = ""
        if file_path not in self.file_locations:
            self.file_locaitons[file_path] = [server_ip,server_port,file_id]
            response += self.ADD_FILE_SUCCESS_RESPONSE
        else:
            response+= self.ADD_FILE_FAILURE_RESPONSE.format("file already exists")
        conn.sendall(response)







def main():
    server = DirectoryServer(PORT, POOL_SIZE)
    server.listen()


if __name__ == "__main__":
    main()