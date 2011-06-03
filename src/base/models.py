from google.appengine.ext import db

class Model(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	created_by = db.UserProperty(auto_current_user_add=True)
	modified_by = db.UserProperty(auto_current_user=True)