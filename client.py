#!/usr/bin/python
import socket
import sys
import os



HOST = ''  # host becomes any address the machine happens to have
PORT = int(sys.argv[1])  # get the port from the command line arguments and convert to int
CLIENT_ROOT = os.getcwd()
BUFFER_SIZE = 2048

class FileClient:

    UPLOAD_MESSAGE = "UPLOAD:{0}\nDATA:{1}\n"
    DOWNLOAD_MESSAGE = "DOWNLOAD:{0}\n"

    def __init__(self):
        self.open_files = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__upload(HOST,444,'1.txt', 'hello.txt')
        self.__download(HOST,444,"1.txt","hello.txt")


    def __upload(self, server_ip, server_port, file_id, file_name):
        """sends a file to be uploaded to the server at server_ip/server_port with the file name file_id"""
        file_path = os.path.join('open_files', file_name)
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
        while ":EOF\n" not in server_response:
            server_response+=self.socket.recv(BUFFER_SIZE)
        file = server_response.splitlines()
        file_id = file[0].split(":")[1]
        file_data = file[1].split(":")[1]
        for line in file[2:]:
            file_data += "\n{}".format(line)
        file_data.replace(":EOF","")
        self.socket.close()



def main():
    client = FileClient()



if __name__ == "__main__":
    main()
