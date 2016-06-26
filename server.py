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
import json
from threading import Thread, Lock
import worker

mutex_db_1 = Lock()
mutex_db_2 = Lock()

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

"""
Form Input Attributes:

1. contacts_send
2. fetch_friends
3. fetch_reviews
4. give_reviews
5. sos_call
6. px
7. py
8. self_id
9. review

"""


def process_args(a, b, c, d, e, self_id, location, review, list_contacts):
    """
    Decisive function to process App side arguments
    and employ server side functionality to make
    things work.
    """
    print a, b, c, d, e
    if a == "on":
        mutex_db_1.acquire() 
        try:
            worker.sync_contacts(self_id, list_contacts, location)
            # Sync contacts
        finally:
            mutex_db_1.release()
    elif b == "on":
        mutex_db_1.acquire()
        try:
            # Fetch location data on contacts
            return worker.fetch_friends_location(self_id, location)
        finally:
            mutex_db_1.release()
    elif c == "on":
        mutex_db_1.acquire()
        mutex_db_2.acquire()
        try:
            # Fetch reviews on areas
            return worker.fetch_reviews_location(self_id, location)
        finally:
            mutex_db_2.release()
            mutex_db_1.release()
    elif d == "on":
        mutex_db_1.acquire()
        mutex_db_2.acquire()
        try:
            # Send reviews about places
            worker.add_review(self_id, location, review)
        finally:
            mutex_db_2.release()
            mutex_db_1.release()
    elif e == "on":
        mutex_db_1.acquire()
        try:
            # For now, we do exactly what we are doing for case 1
            # TODO: WOrk on an alternative approach
            return worker.fetch_friends_location(self_id, location)
        # Send Save Our Souls Call
        finally:
            mutex_db_1.release()
    else:
        mutex_db_1.acquire()
        try:
            # Default: Just sync up location of the user and
            #          set status to online
            worker.sync_location(self_id, location)
        finally:
            mutex_db_1.release()


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
        form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':"POST",
                    'CONTENT_TYPE':self.headers['Content-Type'],
                    },
                keep_blank_values = 1
                )
        logging.warning("==========POST VALUES=========")
        logging.warning("\n")


        # List of all Boolean variables, 1 if True | 0 if False
        print form
        bool_contacts_send = bool_fetch_friends = bool_fetch_reviews =\
                bool_give_reviews = bool_sos_call = ""
        if form.has_key('contacts_send'):
            bool_contacts_send = form['contacts_send'].value
        if form.has_key('fetch_friends'):
            bool_fetch_friends = form['fetch_friends'].value
        if form.has_key('fetch_reviews'):
            bool_fetch_reviews = form['fetch_reviews'].value
        if form.has_key('give_reviews'):
            bool_give_reviews  = form['give_reviews'].value
        if form.has_key('sos_call'):
            bool_sos_call      = form['sos_call'].value

        list_contacts = []
        if form.has_key('contact_file') and form['contact_file'].value != '':
            ret = json.loads(form['contact_file'].value)
            list_contacts = ret['contacts']

        # We will need location and contact number (ID) for any action!
        px = float(form['px'].value)
        py = float(form['py'].value)
        location = tuple([px, py])
        self_id = form['self_id'].value

        # Additional Data
        review = form['review'].value

        ret = {}
        ret['result'] = process_args(bool_contacts_send, bool_fetch_friends,\
                bool_fetch_reviews, bool_give_reviews,\
                bool_sos_call, self_id, location, review, list_contacts)

        # TODO: Check if null
        g = open('send_client.json', 'wb')
        json.dump(ret, g)
        #TODO: And, give result back to client
        self.wfile.write(json.dumps(ret))


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
