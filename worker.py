import os
import ast
from threading import Thread, Lock
import time
import json
import pdb
import operator
import math
from datetime import datetime

"""
Some DEFINES
"""
review_threshold  = 10
friends_threshold = 5
timeout           = 120
all_contacts      = []

""" Alarm DEFINES """
set_alarm_low           = False
set_alarm_med           = False
set_alarm_high          = False
alarm_self_id           = ""
alarm_location          = (0.0, 0.0)
alarm_radius_small      = 50
alarm_radius_large      = 100
selected_alarm_radius   = 0
selected_alarm_contacts = []
allowable_helpers       = 0
max_allowable_helpers   = 1


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
review["(0, 0)"] = {
        '0000000000' : ["This is a good place", 100],
        '1111111111' : ["This is a great place", 200]
}
The members of the list are the review and the timestamp respectively.
"""

# HELPER FUNCTION
def toRad(deg):
    return deg * math.pi / 180.0;

def distance(p1, p2):
    R = 6367
    x = toRad(p2[0]-p1[0])
    y = toRad(p2[1]-p1[1])
    l1 = toRad(p1[0])
    l2 = toRad(p2[0])

    a = math.sin(x/2.0)*math.sin(x/2.0) + (math.sin(y/2.0)*math.sin(y/2.0)) * math.cos(l1) * math.cos(l2)
    print a
    b = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    print b
    d = R * b
    return d

def sync_contacts(self_id, list_contacts, location):
    global timeout, all_contacts
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

    # Updating the global contacts list at the server end
    # and maintain non-duplication
    all_contacts = all_contacts + list_contacts
    all_contacts = list(set(all_contacts))
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    return "contacts sent", False


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
            tmp = {}
            tmp['friend'] = f
            tmp['lat'] = people[f]['location'][0]
            tmp['lon'] = people[f]['location'][1]
            tmp['distance'] = distance(people[f]['location'], center)
            nearby_friends.append(tmp)
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    nearby_friends.sort(key = operator.itemgetter("distance"))
    print nearby_friends
    return nearby_friends, False

"""

Returns an object of the following structure:

{
    'sos' : 0,
    'result' :

    {
        "0" : {
                'lon' : 0,
                'lat' : 1,
                'info': [
                        {
                        'self_id' : "0000000000",
                        'review'  : "This is a nice place",
                        'time'    : 1000000
                        }
                        {
                        'self_id' : "1111111111",
                        'review'  : "This is a nice place",
                        'time'    : 1000000
                        }
                        ...
                ]
        }
    }
}
"""
def fetch_reviews_location(self_id, location):
    global timeout, review_threshold
    with open('reviews.json', 'rb') as g:
        reviews = json.load(g)
    with open('people.json', 'rb') as g:
        people = json.load(g)
    nearby_reviews = {}
    tmp = []
    i = 0
    for str_locn in reviews.keys():
        tmp = {}
        tmp['info'] = []
        locn = ast.literal_eval(str_locn)
        if distance(locn, location) < review_threshold:
            for idx in reviews[str_locn]:
                info = {}
                print str(list(locn))
                info['self_id'] = idx
                info['review']  = reviews[str_locn][idx][0]
                print idx
                print reviews[str_locn][idx]
                info['time']    = datetime.fromtimestamp(reviews[str_locn][idx][1]).strftime('%Y-%m-%d %H:%M:%S')
                tmp['info'].append(info)
            tmp['lat'] = locn[0]
            tmp['lon'] = locn[1]
        if len(tmp['info']) > 0:
            nearby_reviews[i] = tmp
        i += 1
    # Need to update online status!
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()
    for f in people[self_id]['friends']:
        # Mandatory Online/Offline refresh
        if people[f]['online'] and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    print nearby_reviews
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    with open('reviews.json', 'wb') as g:
        json.dump({str(k): v for k, v in reviews.iteritems()}, g)

    return nearby_reviews, False

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
    return [], False


def sync_location(self_id, location):
    global timeout, set_alarm, alarm_location, selected_alarm_radius, selected_alarm_contacts, alarm_self_id
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
    return ["ok"], False

def handle_notifs(self_id):
    global timeout, set_alarm, alarm_location, selected_alarm_radius, selected_alarm_contacts, alarm_self_id, set_alarm_low, set_alarm_high, set_alarm_med
    with open('people.json', 'rb') as g:
        people = json.load(g)
    print "Notification Change"
    if not people.has_key(self_id):
        print "Contacts not synced. Proceed."
        return ["no"], False
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = now = time.time()

    # Mandatory Online/Offline refresh
    for f in people[self_id]['friends']:
        if people[f]['online'] and people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    location = people[self_id]['location']
    # TODO: Place a caveat as a guard condition
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    response = {}
    print "Alarm status ", set_alarm_low, set_alarm_med, set_alarm_high
    if location is None or alarm_location is None:
        print "Location not updated yet. Will check for SOS on next retry."
        return ["no"], False
    print "alarm = ", alarm_self_id
    if (set_alarm_low or set_alarm_med or set_alarm_high) and self_id != alarm_self_id:
        # Check if alarm is set and this is another person

        # Check if the person is in the allowable list of contacts and is within the 
        # acceptable circle.
        print selected_alarm_contacts

        if self_id in selected_alarm_contacts:
            print "In"
            print alarm_location, location, distance(alarm_location, location), selected_alarm_radius
            if distance(alarm_location, location) <= selected_alarm_radius:
                # This person could be our helper.
                print "Danger, Help the person!"
                response['self_id'] = alarm_self_id
                response['lat']     = alarm_location[0]
                response['lon']     = alarm_location[1]

                # In the absence of any alarm, send an "ok" response
                return response, True
    return ["ok"], False

def sos_call(self_id, low, med, high):
    global set_alarm_low, set_alarm_med, set_alarm_high, alarm_radius_small, selected_alarm_radius, \
            alarm_radius_large, selected_alarm_contacts, alarm_location, alarm_self_id, all_contacts
    # When this happens, reassure the person who wants help
    with open('people.json', 'rb') as g:
        people = json.load(g)
    help_msg = "We are dispatching help. Please stay calm and be alert."
    location = people[self_id]['location']
    if low == "on":
        set_alarm_low = True
        selected_alarm_radius = alarm_radius_small
        selected_alarm_contacts = people[self_id]['friends']
    elif med == "on":
        set_alarm_med = True
        selected_alarm_radius = alarm_radius_small
        selected_alarm_contacts = people[self_id]['friends']
    elif high == "on":
        set_alarm_high = True
        selected_alarm_radius = alarm_radius_large
        selected_alarm_contacts = all_contacts

    alarm_location = location
    alarm_self_id = self_id
    print alarm_self_id
    return [help_msg], False

def handle_user_help_response(self_id, location, on_or_off):
    global allowable_helpers, max_allowable_helpers, set_alarm_med, set_alarm_low, set_alarm_high
    msg = "Another user has already been selected. Thank you for your intent."
    if on_or_off == "on":
        if allowable_helpers < max_allowable_helpers and (set_alarm_low or set_alarm_med or set_alarm_high):
            # User has acknowledged to help and the alarm status is still active
            allowable_helpers += 1
            # Now, set the alarm off, this we are doing currently as we need only a single person to help
            if allowable_helpers == max_allowable_helpers:
                set_alarm_high = set_alarm_med = set_alarm_low = False

            msg = "You have been selected for this mission. Please proceed."


    if on_or_off == "off":
        # User has declined to help
        msg = "Thank you for your reply."

    return msg, False

if __name__ == '__main__':
    main()
