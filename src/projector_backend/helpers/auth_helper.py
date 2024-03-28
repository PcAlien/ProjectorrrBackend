import os

global username

username = os.environ.get('user')
username = username.split("\\")[-1]
