from google.appengine.ext import db
import base.models

class Mine(base.models.Model):
    user = db.UserProperty(required=True)
    search = db.StringProperty()
    url = db.StringProperty()
    count = db.IntegerProperty(default=0)
    last_count = db.IntegerProperty(default=0)
    
    def to_dict(self):
        return {'key':str(self.key()),
                'search':self.search,
                'count':self.count}

class Tweet(base.models.Model):
    mine = db.ReferenceProperty(reference_class=Mine, collection_name='tweets')
    id = db.StringProperty()
    text = db.TextProperty()
    date = db.DateTimeProperty()
    
    def to_dict(self):
        return {'key':str(self.key()),
                'date':self.date.strftime("%d/%m/%y %H:%M:%S"),
                'text':self.text}