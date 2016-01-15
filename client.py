#!/usr/bin/python
import socket
import sys
import os



HOST = ''  # host becomes any address the machine happens to have
PORT = int(sys.argv[1])  # get the port from the command line arguments and convert to int
BUFFER_SIZE = 2048

class FileClient:

    UPLOAD_MESSAGE = "UPLOAD:{0}\nDATA:{1}\n\n"
    DOWNLOAD_MESSAGE = "DOWNLOAD:{0}\n\n"
    DIRECTORY_SERVER_REQUEST = "GET FILE:{0}\n\n"
    LOCK_REQUEST_MESSAGE = "GET_LOCK:{0}\n\n"
    FREE_LOCK_MESSAGE = "RELEASE_LOCK:{0}\n\n"
    DIRECTORY_SERVER_IP = ''

    DIRECTORY_SERVER_PORT = 6666
    CLIENT_ROOT = os.getcwd()
    OPEN_FILES_PATH = CLIENT_ROOT+"/open_files"


    def __init__(self):
        self.open_files = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.__upload(HOST,444,'1.txt', 'hello.txt')

        self.__upload(HOST,6667,'1.txt','hello.txt')

    def openFile(self,file_path):
        if file_path not in self.open_files.values():
            """asks directory service for the file location and then downloads the file"""
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.DIRECTORY_SERVER_IP,self.DIRECTORY_SERVER_PORT))
            self.socket.sendall(self.DIRECTORY_SERVER_REQUEST.format(file_path))
            server_response = ""
            while "\n\n" not in server_response:
                server_response += self.socket.recv(BUFFER_SIZE)
            self.socket.close()
            if "ERROR" in server_response:
                print server_response
            else:
                text = server_response.splitlines()
                server_ip = text[0].split(":")[1]
                server_port = int(text[1].split(":")[1])
                file_id = text[2].split(":")[1]
                lock_server_ip = text[3].split(":")[1]
                lock_server_port = text[4].split(":")[1]
                while self.__getLock(file_id, lock_server_ip, lock_server_port) == False:
                    self.sleep(100)
                self.__download(server_ip, server_port, file_id, file_path)
                self.open_files[file_id] = file_path
                self.__releaseLock(file_id, lock_server_ip, lock_server_port)

    def __releaseLock(self,file_id, lock_server_ip, lock_server_port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((lock_server_ip, lock_server_port))
        self.socket.sendall(self.FREE_LOCK_MESSAGE.format(file_id))

    def __getLock(self,file_id, lock_server_ip, lock_server_port):
        request = self.LOCK_REQUEST_MESSAGE.format(file_id)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((lock_server_ip, lock_server_port))
        self.socket.sendall(request)
        server_response = ''
        lock_granted = False
        while "\n\n" not in server_response:
            server_response+=self.socket.recv(BUFFER_SIZE)
        if server_response.startswith("LOCK_GRANTED"):
            lock_granted = True
        self.socket.close()
        return lock_granted


    def __upload(self, server_ip, server_port, file_id, file_name):
        """sends a file to be uploaded to the server at server_ip/server_port with the file name file_id"""
        file_path = os.path.join(self.OPEN_FILES_PATH, file_name)
        with open(file_path, 'r') as file:
            file_data  = file.read()
            upload_data = self.UPLOAD_MESSAGE.format(file_id,file_data)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_ip, server_port))
            self.socket.sendall(upload_data)
            self.socket.close()
            print upload_data

    def __download(self,server_ip, server_port, file_id, file_name):
        """requests a server from a file with the file id file_id"""
        request = self.DOWNLOAD_MESSAGE.format(file_id)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip,server_port))
        self.socket.sendall(request)

        server_response = ""
        while ":EOF\n\n" not in server_response:
            server_response+=self.socket.recv(BUFFER_SIZE)
        file = server_response.splitlines()
        file_id_returned = file[0].split(":")[1]
        file_data = file[1].split(":")[1]
        for line in file[2:]:
            file_data += "\n{}".format(line)
        file_data = file_data.replace(":EOF","")
        self.socket.close()
        file_path = os.path.join(self.OPEN_FILES_PATH, file_name)
        with open(file_path, 'wr') as open_file:
            open_file.write(file_data)






def main():
    client = FileClient()



if __name__ == "__main__":
    main()
