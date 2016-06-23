#!/usr/bin/python

'''
Run the file on another port on the localhost by the following command
>> python server.py 0.0.0.0 8001
More importantly, 
>> python <ip_addr> <port>

Schedule a cronjob for it to run this file at stipulated timings
'''

import SimpleHTTPServer
from OpenSSL import SSL
import SocketServer
import logging
import cgi
import os
import sys, thread
from subprocess import call
import sched, time
import BaseHTTPServer
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
import socket

'''
Port handling
'''
if len(sys.argv) > 2:
    PORT = int(sys.argv[2])
    I = sys.argv[1]
elif len(sys.argv) > 1:
    PORT = int(sys.argv[1])
    I = ""
else:
    # Since it is a HTTPS server now, the 
    # default port is 443.
    PORT = 443
    I = ""

#TODO: Do DB work here.
files = [f for f in os.listdir('.') if os.path.isfile(f)]
for f in files:
    if f=='server.log':
        os.remove('server.log')

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
    def do_GET(self):
        logging.warning("===========GET STARTED===========")
        logging.warning(self.headers)
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200, 'OK')                       # Handshaking Signals
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        form = open('form.html', 'r')
        self.wfile.write(form.read())
    def do_POST(self):
        logging.warning("==========POST STARTED===========")
        logging.warning(self.headers)
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200, 'OK')                       #Handshaking Signals
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        reply = open('reply.html', 'r')
        self.wfile.write(reply.read())
        form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':"POST",
                'CONTENT_TYPE':self.headers['Content-Type'],
                })
        logging.warning("==========POST VALUES=========")
        logging.warning("\n")

        # User authentication
        auth = form.getvalue('auth')            # To be given in the class as an OTP
        roll = form.getvalue('roll')            # Roll no. of the student
        password = form.getvalue('pass')        # Some kind of password alloted to a student

        print auth, roll, password
        #TODO: Perform checking and validation, and increase the ref count
        if auth == str(auth_otp):
            g.write(roll+"\t"+password+"\n")
            time.sleep(10)

        print "Completing attendance"

class SecureThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """ Handles Multi-Threaded HTTP Server requests """
    def __init__(self, server_address, HandlerClass):
        """ Utilize IP address, Port no. """
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        #server.pem's location (containing the server private key and
        #the server certificate).
        fpem = 'certs/server.pem'
        ctx.use_privatekey_file (fpem)
        ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        request.shutdown()

def main(timeout_mins):
    Handler = ServerHandler

    httpd = SecureThreadedHTTPServer(("", PORT), Handler)

    print "Python https server version 0.1"
    print "Serving at https://%(interface)s:%(port)s" % dict(interface=I or "localhost", port=PORT)
    tick = time.time()
    thread.start_new_thread(httpd.serve_forever,())
    while 1:
        if time.time() > tick + 60*timeout_mins:
            print "Timeout"
            httpd.shutdown()
            break

if __name__ == "__main__":
    main(10)
