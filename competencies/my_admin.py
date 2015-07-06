"""Functions that help administer the site."""
import os

#from django.contrib.auth import createsuperuser
from django.contrib.auth.models import User
from django.db import IntegrityError

from competencies.models import *

def add_userprofile(user):
    """Make a new userprofile, and connect it to a new user."""
    new_userprofile = UserProfile()
    new_userprofile.user = user
    new_userprofile.save()

    
    
def initialize_data():
    """For use when re-creating the db locally."""
    # To use this, import into django shell and run it.

    # Create superuser, and regular user.
    try:
        su = User.objects.create_superuser(username=os.environ['SU_USERNAME'],
                                           password=os.environ['SU_PASSWORD'],
                                           email='')
        add_userprofile(su)
    except IntegrityError:
        print('The user %s already exists.' % os.environ['SU_USERNAME'])
        su = User.objects.filter(username=os.environ['SU_USERNAME'])[0]

    try:
        ru = User.objects.create_user(username=os.environ['RU_USERNAME'],
                                      password=os.environ['RU_PASSWORD'])
        add_userprofile(ru)
    except IntegrityError:
        print('The user %s already exists.' % os.environ['RU_USERNAME'])
        ru = User.objects.filter(username=os.environ['RU_USERNAME'])[0]

    build_sample_school(ru)

def build_sample_school(owner):
    """Build the sample school."""
    school = Organization.objects.create(name='Sample School', owner=owner)
    owner.userprofile.organizations.add(school)

