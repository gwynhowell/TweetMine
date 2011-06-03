from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.key_range import simplejson
from google.appengine.ext.webapp import template
import os

class PageBase(webapp.RequestHandler):
    template_values = {}
    requires_login = True

    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.template_values = {}
    
    def initialize(self, request, response):
        webapp.RequestHandler.initialize(self, request, response)
        
        self.google_user = users.get_current_user()
        if not self.google_user:
            if self.requires_login:
                self.redirect(users.create_login_url(self.request.uri))
                return False
            else:
                self.template_values['login_url'] = users.create_login_url(self.request.uri)
        else:
            self.email = self.google_user.email()
            self.domain = self.google_user.auth_domain
            self.template_values['logout_url'] = users.create_logout_url('/')
            self.template_values['domain'] = self.domain
            self.template_values['email'] = self.email
        return True

    def render(self, path):
        dir_name = os.path.dirname(__file__)
        dir_name = dir_name[:-len('base')]
        template_path = os.path.join(dir_name, 'templates/%s' % path)
        self.response.out.write(template.render(template_path, self.template_values))
        
    def load_object_from_request(self):
        path = self.request.path
        if path[-1] == '/':
            path = path[:-1]
        bits = path.split('/')
        if bits:
            try:
                return db.get(bits[-1])
            except:
                return None
        
class XhrBase(webapp.RequestHandler):
    requires_login = True
    
    def get(self):        
        self.handle_request()
            
    def post(self):        
        self.handle_request()
        
    def initialize(self, request, response):
        webapp.RequestHandler.initialize(self, request, response)
        
        self.google_user = users.get_current_user()
        if not self.google_user and self.requires_login:
            self.error(401)
            return
        else:
            self.email = self.google_user.email()
            self.domain = self.google_user.auth_domain
                
    def handle_request(self):
        request = self.request.path.split('/')
        request = request[len(request)-1]
        
        if hasattr(self, request):
            result = getattr(self, request)()
            response = simplejson.dumps(result)
            self.response.out.write(response)
        else:
            self.error(404)