import getpass

from mongoengine import *

from models import User

connect('lumi')

username = raw_input("Username: ")
admin = User(username=username)

password = getpass.getpass()
admin.set_password(password)

print "Admin user", username, "created."
