import os
import ast
from threading import Thread, Lock
import time
import json

"""
Some DEFINES
"""
review_threshold  = 10
friends_threshold = 5
timeout           = 1000
set_alarm         = False


"""
FORMAT of the "People" Database

The people's database has the self location and the list of friends, hashable by contact no.

The database needs to be consistent, i.e. there should be
an entry for every friend of yours, even if we have or do
not have his/her location/data.

people = {}
people["0000000000"] = {
        'location': (0, 0),
        'friends': ["1111111111", "2222222222"],
        'online': 1,
        'time_updated': 0
        }
people["1111111111"] = {
        'location': (0, 1),
        'friends': ["0000000000", "2222222222"],
        'online': 0,
        'time_updated': 0
        }
people["2222222222"] = {
        'location': (1, 0),
        'friends': ["1111111111", "0000000000"],
        'online': 1,
        'time_updated': 0
         }

FORMAT of the "Reviews" Database

The reviews database has the self location and list of reviews, hashable by location.

reviews = {}
review[(0, 0)] = {
        '0000000000' : ["This is a good place", 100],
        '1111111111' : ["This is a great place", 200]
}
The members of the list are the review and the timestamp respectively.
"""

# HELPER FUNCTION
def distance(p1, p2):
    return ((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)**0.5

def sync_contacts(self_id, list_contacts, location):
    global timeout
    with open('people.json', 'rb') as g:
        people = json.load(g)
    dummy = {
        'location': None,\
        'friends': [self_id],\
        'online': 0,\
        'time_updated': 0\
        }
    if people.get(self_id) is None:
      people[self_id] = dummy
    people[self_id]['friends'] = list_contacts
    people[self_id]['location'] = location
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()

    dummy = {
        'location': None,\
        'friends': [self_id],\
        'online': 0,\
        'time_updated': 0\
        }
    # Handle all contacts which have had no prev data
    for contact in list_contacts:
        if people.get(contact) is None:
            people[contact] = dummy

    # Mandatory Online/Offline refresh
    for f in people[self_id]['friends']:
        if people[f]['online'] == 1 and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()

    with open('people.json', 'wb') as g:
        json.dump(people, g)


def fetch_friends_location(self_id, location):
    global timeout
    with open('people.json', 'rb') as g:
        people = json.load(g)
    # Set the location
    people[self_id]['location'] = location
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()
    center = location
    friends = people[self_id]['friends']
    nearby_friends = []

    for f in friends:
        # Mandatory Online/Offline refresh
        if people[f]['online'] == 1 and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
        if people[f]['online'] and distance(people[f]['location'], center) <= friends_threshold:
            nearby_friends.append([f, people[f]['location']])
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    return nearby_friends

def fetch_reviews_location(self_id, location):
    global timeout, review_threshold
    with open('reviews.json', 'rb') as g:
        reviews = json.load(g)
    with open('people.json', 'rb') as g:
        people = json.load(g)
    nearby_reviews = []
    for str_locn in reviews.keys():
        locn = ast.literal_eval(str_locn)
        if distance(locn, location) < review_threshold:
            for idx in reviews[str_locn]:
                nearby_reviews.append([idx, reviews[str_locn][idx][0], reviews[str_locn][idx][1]])

    # Need to update online status!
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()
    for f in people[self_id]['friends']:
        # Mandatory Online/Offline refresh
        if people[f]['online'] and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    with open('reviews.json', 'wb') as g:
        json.dump({str(k): v for k, v in reviews.iteritems()}, g)
    return nearby_reviews

def add_review(self_id, location, review):
    global timeout, review_threshold
    with open('reviews.json', 'rb') as g:
        reviews = json.load(g)
    reviews[str(location)] = {\
        self_id : [review, time.time()]\
        }
    print reviews
    
    with open('people.json', 'rb') as g:
        people = json.load(g)
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()

    for f in people[self_id]['friends']:
        # Mandatory Online/Offline refresh
        if people[f]['online'] and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    with open('reviews.json', 'wb') as g:
        json.dump({str(k): v for k, v in reviews.iteritems()}, g)

def sync_location(self_id, location):
    global timeout, set_alarm
    with open('people.json', 'rb') as g:
        people = json.load(g)
    people[self_id]['location'] = location
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()

    # Mandatory Online/Offline refresh
    for f in people[self_id]['friends']:
        if people[f]['online'] and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    if set_alarm:
        # TODO: Decide what to do here.

def sos_call(self_id, location):
    global set_alarm = True
    # When this happens, reassure the person who wants help
    help_msg = "We are dispatching help. Please stay calm and be alert."
    return help_msg
if __name__ == '__main__':
    main()
