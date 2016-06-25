import os
from threading import Thread, Lock
import time

"""
Some DEFINES
"""
radius_threshold = 5


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
# TODO: load the Actual database from a file


def sync_contacts(self_id, list_contacts, location):
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


def fetch_friends_location(self_id, location):

if __name__ == '__main__':
    main()
