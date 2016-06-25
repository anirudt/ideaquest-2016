import os
from threading import Thread, Lock
import time
import json

"""
Some DEFINES
"""
radius_threshold = 5
timeout          = 1000


"""
FORMAT of the "People" Database

The people's database has the self location and the list of friends.

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
"""

# HELPER FUNCTION
def distance(p1, p2):
    return ((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)**0.5

def sync_contacts(self_id, list_contacts, location):
    with open('people.json', 'rb') as g:
        people = json.load(g)
    people[self_id]['friends'] = list_contacts
    people[self_id]['location'] = location
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = time.time()

    # Handle all contacts which have had no prev data
    dummy = {
        'location': None,\
        'friends': [self_id],\
        'online': 0,\
        'time_updated': 0\
        }
    for contact in list_contacts:
        if people.get(contact) is None:
            people[contact] = dummy
            people[contact][time_updated] = time.time()

    # Mandatory Online/Offline refresh
    for f in people[self_id]['friends']:
        if people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()

    with open('people.json', 'wb') as g:
        json.dump(people, g)


def fetch_friends_location(self_id, location):
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
        if people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
        if people[f]['online'] && distance(people[f]['location'], center) <= threshold:
            nearby_friends.append([self_id, people[f]['location']])
    with open('people.json', 'wb') as g:
        json.dump(people, g)
    return nearby_friends


def sync_location(self_id, location):
    with open('people.json', 'rb') as g:
        people = json.load(g)
    people[self_id]['location'] = location
    people[self_id]['online'] = 1
    people[self_id]['time_updated'] = time.time()

    # Mandatory Online/Offline refresh
    for f in people[self_id]['friends']:
        if people[f]['time_updated'] - now > timeout:
            people[f]['online'] = 0
            people[f]['time_updated'] = time.time()
    with open('people.json', 'wb') as g:
        json.dump(people, g)

if __name__ == '__main__':
    main()
