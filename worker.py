import os

#TODO: Do DB work here.
files = [f for f in os.listdir('.') if os.path.isfile(f)]
for f in files:
    if f=='server.log':
        os.remove('server.log')

