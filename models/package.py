from google.appengine.ext import db

class Package(db.Model):
    owner = db.UserProperty(auto_current_user_add = True)
    name = db.StringProperty()

    @classmethod
    def exists(cls, name):
        return len(cls.all().filter('name =', name).fetch(1)) != 0
