from google.appengine.ext import db

class Package(db.Model):
    owner = db.UserProperty()
    name = db.StringProperty()
