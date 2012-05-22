from google.appengine.ext import db

class Package(db.Model):
    owner = db.UserProperty(auto_current_user_add = True)
    name = db.StringProperty()

    def __init__(self, *args, **kwargs):
        kwargs['key_name'] = kwargs['name']
        super(Package, self).__init__(*args, **kwargs)

    @classmethod
    def exists(cls, name):
        return cls.get_by_key_name(name) is not None

    @classmethod
    @db.transactional
    def create_unless_exists(cls, name):
        if cls.exists(name):
            return False

        cls(name = name).put()
        return True
