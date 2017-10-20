#! python3
#This program is a basic TCP proxy server built on the socketserver.TCPServer class
#
import socketserver, socket, select, time
from netpack import nbsocket

remote_addr = ''
remote_port = None
stop_server = False
timeout = 3.0

#define the handler for each thread the TCPproxyserver
class TCPproxyhandler(socketserver.BaseRequestHandler):
    def setup(self):
        global remote_addr
        global remote_port
        self.socklist = []
        try:
            self.rem_nbs = nbsocket.Nbsocket()
            self.rem_nbs.connect(remote_addr, remote_port)
            self.socklist.append(self.rem_nbs.socket())
        except Exception as e:
            self.rem_nbs.close()
            print("{}. {}".format(type(e), e))
    def handle(self):
        #buffer for data coming from the remote server
        inbuffer = bytearray()
        #buffer for data headed for the remote server
        outbuffer = bytearray()
        self.request.setblocking(0)
        local_sock = self.request
        self.socklist.append(local_sock)
        global timeout
        t1 = time.time()
        while True:
            try:
                read, write, err = select.select(self.socklist,self.socklist,self.socklist,2.0)
                for s in read:
                    if s is local_sock:
                    #the local socket can receive
                        data = local_sock.recv(1024)
                        if data:
                            outbuffer.extend(data)
                            print("data ready from remote")
                            t1 = time.time()
                    if s is self.rem_nbs.socket():
                    #the remote socket can receive
                        data = self.rem_nbs.socket().recv(1024)
                        if data:
                            inbuffer.extend(data)
                            print("data ready from local")
                            t1 = time.time()
                for s in write:
                    if s is local_sock and len(inbuffer):
                    #the local socket can write and data has been received from the remote server
                        b_in = bytes(inbuffer)
                        local_sent = local_sock.send(b_in)
                        if local_sent:
                            inbuffer = inbuffer[local_sent:]
                            t1 = time.time()
                        print("{} bytes relayed to local".format(local_sent))
                    if s is self.rem_nbs.socket() and len(outbuffer):
                    #the remote socket can write and data has been received from the local application
                        b_out = bytes(outbuffer)
                        rem_sent = self.rem_nbs.socket().send(b_out)
                        if rem_sent:
                            outbuffer = outbuffer[rem_sent:]
                            t1 = time.time()
                        print("{} bytes relayed to remote".format(rem_sent))
                for s in err:
                    print("Error triggered.")
                    break
                global stop_server
                if stop_server:
                    self.rem_nbs.close()
                    print("Stoping handler loop\n")
                    break
                t2 = time.time()
                if t2 - t1 > timeout:
                    self.rem_nbs.close()
                    print("thread timeout")
                    break
            except Exception as e:
                print("{}. {}".format(type(e), e))
                break
    def finish(self):
        try:
            self.rem_nbs.close()
        except Exception as e:
            print("{}. {}".format(type(e), e))

#define the TCPproxyserver class
class TCPproxyserver(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    #Remote server address and port
    remote_addr = input("Enter remote server address: ")
    str_port = input("Enter remote port: ")
    #convert the port number to an integer
    if str_port.isnumeric():
        remote_port = int(str_port)
    else:
        exit()
    print("Starting up Proxy Server...")
    try:
        #initialize the Proxy server
        proxy = TCPproxyserver(("127.0.0.1", remote_port),TCPproxyhandler)
        #start accepting threads
        proxy.serve_forever()
    except KeyboardInterrupt as e:
        stop_server = True
        proxy.shutdown()
        print("Stopping proxy Server")
