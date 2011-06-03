from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from tweetmine import models, tasks

class CronHandler(webapp.RequestHandler):
    def get(self):
        self.post()
        
    def post(self):
        mines = models.Mine.all().fetch(1000)
        for mine in mines:
            tasks.MineTweets.fire(key=str(mine.key()))
        
application = webapp.WSGIApplication(
                                     [
                                      ('/cron', CronHandler),
                                      ], debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()