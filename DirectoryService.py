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



class ChatServer:
    """a chat server with several chat rooms"""

    def __init__(self, port, num_thread):
        self.users_in_rooms = {}  # stores all roomid and the clients in those rooms {[RoomId : {[clientId:conn],{[clientId1:conn]}],.....]}
        self.rooms = {}  # stores all rooms and their ids in the form {[room_id:room_name], ... }
        self.users = {}  # keeps a list of all users who have used the chatserver in form [name:id]
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
            elif data.startswith("JOIN_CHATROOM") and data.endswith("\n"):
                self.joinRoom(data, conn)
            elif data.startswith("LEAVE_CHATROOM") and data.endswith("\n"):
                self.leaveRoom(data, conn)
            elif data.startswith("CHAT") and data.endswith("\n"):
                self.chat(data, conn)
            elif data.startswith("DISCONNECT") and data.endswith("\n"):
                self.disconnectUser(data, conn)

    def chat(self,data,conn):
        """sends a message from a user to all other users in a given chatroom using sendMessageToRoom"""
        text = data.splitlines()
        room_id = int(text[0].split(":")[1])
        client_name = text[2].split(":")[1]
        message_from_client = text[3].split(":")[1]
        message_to_send = "CHAT: {0}\nCLIENT_NAME: {1}\nMESSAGE: {2}\n\n".format(str(room_id),client_name,message_from_client)
        self.sendMessageToRoom(message_to_send,room_id)


    def disconnectUser(self,data,conn):
        """sends a leave message to every room the given client is in and then terminates their connection"""
        text = data.splitlines()
        client_name = text[2].split(":")[1]
        if client_name in self.users:
            client_id = self.users[client_name]
            room_keys = sorted(self.users_in_rooms.keys())
            for room in room_keys:
                if client_id in self.users_in_rooms[room]:
                    room_leave_message = "LEAVE_CHATROOM: {0}\nJOIN_ID: {1} \nCLIENT_NAME: {2}\n\n".format(str(room),str(client_id),client_name)
                    self.leaveRoom(room_leave_message)
        conn = None


    def leaveRoom(self,data, conn=None):
        """sends a message to every user in the given room that the client has left and sends the client a confirmation message,unless
            they are disconnecting"""
        text = data.splitlines()
        room_id = int(text[0].split(":")[1])
        client_id = int(text[1].split(":")[1])
        client_name = text[2].split(":")[1]
        if conn: #when disconnecting this message is not sent
            conn.sendall("LEFT_CHATROOM: {0}\nJOIN_ID: {1}\n".format(str(room_id),str(client_id)))
        if client_id in self.users_in_rooms[room_id]:
            room_leave_message = "CHAT: {0}\nCLIENT_NAME: {1}\nMESSAGE:{1} has left this chatroom.\n\n".format(str(room_id),client_name)
            self.sendMessageToRoom(room_leave_message,room_id)
            del self.users_in_rooms[room_id][client_id]

    def joinRoom(self, data, conn):
        """adds a user to a room and sends a message to everyone in that room to notify them
            if the room does not exist then it is created"""
        text = data.splitlines()
        room_name = text[0].split(":")[1]
        client_name = text[3].split(":")[1]
        room_id = int(hashlib.md5(room_name).hexdigest(), 16)
        client_id = int(hashlib.md5(client_name).hexdigest(), 16)
        if client_id not in self.users:
            self.users[client_name] = client_id
        if room_id not in self.users_in_rooms:
            self.users_in_rooms[room_id] = dict()
            self.rooms[room_id] = room_name
        if client_id in self.users_in_rooms[room_id]:
            conn.sendall("ERROR_CODE: {0}\nERROR_DESCRIPTION: Client already in room".format(1))
        else:
            self.users_in_rooms[room_id][client_id] = conn
            conn.sendall("JOINED_CHATROOM: {0}\nSERVER_IP: {1}\nPORT: {2}\nROOM_REF: {3}\nJOIN_ID: {4}\n".format(str(room_name), IP,
                                                                                                        str(PORT),
                                                                                                        str(room_id),
                                                                                                        str(client_id)))
            room_join_message = "CHAT: {0}\nCLIENT_NAME: {1}\nMESSAGE: {1} has joined this chatroom.\n\n".format(str(room_id),client_name)
            self.sendMessageToRoom(room_join_message,room_id)

    def sendMessageToRoom(self, message, room_id):
        """sends a given message to all clients in a given chatroom"""
        for users in self.users_in_rooms[room_id]:
            self.users_in_rooms[room_id][users].sendall(message)


def main():
    server = ChatServer(PORT, POOL_SIZE)
    server.listen()


if __name__ == "__main__":
    main()