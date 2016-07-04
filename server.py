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
5. sos_call_low
6. sos_call_med
7. sos_call_high
8. px
9. py
10. self_id
11. review
12. contact_file

"""

#TODO: If DBs are not created, create sample ones.

def process_args(bool_args, self_id, location, review, list_contacts):
    """
    Decisive function to process App side arguments
    and employ server side functionality to make
    things work.
    """
    if bool_args[0] == "on":
        mutex_db_1.acquire() 
        try:
            ret = worker.sync_contacts(self_id, list_contacts, location)
            # Sync contacts
        finally:
            mutex_db_1.release()
    elif bool_args[1] == "on":
        mutex_db_1.acquire()
        try:
            # Fetch location data on contacts
            ret = worker.fetch_friends_location(self_id, location)
        finally:
            mutex_db_1.release()
    elif bool_args[2] == "on":
        mutex_db_1.acquire()
        mutex_db_2.acquire()
        try:
            # Fetch reviews on areas
            ret = worker.fetch_reviews_location(self_id, location)
        finally:
            mutex_db_2.release()
            mutex_db_1.release()
    elif bool_args[3] == "on":
        mutex_db_1.acquire()
        mutex_db_2.acquire()
        try:
            # Send reviews about places
            ret = worker.add_review(self_id, location, review)
        finally:
            mutex_db_2.release()
            mutex_db_1.release()
    elif bool_args[4] == "on" or bool_args[5] == "on" or bool_args[6] == "on":
        mutex_db_1.acquire()
        try:
            # For now, we do exactly what we are doing for case 1
            # TODO: WOrk on an alternative approach
            ret = worker.sos_call(self_id, location, bool_args[4], bool_args[5], bool_args[6])
        # Send Save Our Souls Call
        finally:
            mutex_db_1.release()
    elif bool_args[7] == "on" or bool_args[7] == "off":
        mutex_db_1.acquire()
        try:
            # Handle when the user acks or nacks to help
            ret = worker.handle_user_help_response(self_id, location, bool_args[7])
        finally:
            mutex_db_1.release()

    elif location is not None:
        mutex_db_1.acquire()
        try:
            # Default: Just sync up location of the user and
            #          set status to online
            ret = worker.sync_location(self_id, location)
        finally:
            mutex_db_1.release()

    else:
        mutex_db_1.acquire()
        try:
            ret = worker.handle_notifs(self_id)
        finally:
            mutex_db_1.release()
    return ret


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
                bool_give_reviews = ""
        bool_sos_call_low = bool_sos_call_med = bool_sos_call_high = ""
        bool_ack_help = ""

        if form.has_key('contacts_send'):
            bool_contacts_send = form['contacts_send'].value
        if form.has_key('fetch_friends'):
            bool_fetch_friends = form['fetch_friends'].value
        if form.has_key('fetch_reviews'):
            bool_fetch_reviews = form['fetch_reviews'].value
        if form.has_key('give_reviews'):
            bool_give_reviews  = form['give_reviews'].value
        if form.has_key('sos_call_low'):
            bool_sos_call_low  = form['sos_call_low'].value
        if form.has_key('sos_call_med'):
            bool_sos_call_med  = form['sos_call_med'].value
        if form.has_key('sos_call_high'):
            bool_sos_call_high = form['sos_call_high'].value
        if form.has_key('ack_help'):
            bool_ack_help      = form['ack_help'].value

        list_contacts = []
        review = ""
        if form.has_key('contact_file') and form['contact_file'].value != '':
            ret = json.loads(form['contact_file'].value)
            list_contacts = ret

        # We will need location and contact number (ID) for any action!
        px, py = "", ""
        if form['px'].value != "":
            px = float(form['px'].value)
        if form['py'].value != "":
            py = float(form['py'].value)
        if px == "" and py == "":
            location = None
        else:
            location = tuple([px, py])
        self_id = ""
        if form.has_key('self_id'):
            self_id = form['self_id'].value

        # Additional Data
        if form.has_key('review'):
            review = form['review'].value

        ret = {}
        print bool_contacts_send, bool_fetch_friends, bool_fetch_reviews, bool_give_reviews, bool_sos_call_low, bool_sos_call_med, bool_sos_call_high, \
        bool_ack_help, self_id, location, review, list_contacts
        a, b = process_args([bool_contacts_send, bool_fetch_friends, bool_fetch_reviews, bool_give_reviews, bool_sos_call_low, bool_sos_call_med, bool_sos_call_high, bool_ack_help], self_id, location, review, list_contacts)

        # TODO: Check if null
        ret['result'] = a
        if b:
            ret['sos'] = 1
        else:
            ret['sos'] = 0
        # Scan for the above key on the app side for helping an SOS Victim
        #TODO: And, give result back to client
        self.wfile.write(json.dumps(ret))


class SecureThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, HandlerClass):
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
    main(100)
