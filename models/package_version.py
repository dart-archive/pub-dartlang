from google.appengine.ext import db
from package import Package

class PackageVersion(db.Model):
    version = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    contents = db.BlobProperty()
    package = db.ReferenceProperty(Package,
                                   collection_name = "package_version_set")
