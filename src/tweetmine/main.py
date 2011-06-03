from django.utils import simplejson
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from tweetmine import models, tasks
import base.handlers

class PageBase(base.handlers.PageBase):
    pass

class XhrBase(base.handlers.XhrBase):
    pass

class AddSearch(PageBase):
    def get(self):
        search = self.request.get('search')
        models.Mine(search=search).put()
        self.response.out.write('Added ' + search)
        
class RemoveSearch(PageBase):
    def get(self):
        search = self.request.get('search')
        stuff = models.Mine.gql('WHERE search = :1', search).fetch(100)
        if stuff:
            db.delete(stuff)
        self.response.out.write('Deleted ' + search)


class TweetsPage(PageBase):
    def get(self):
        mine = self.load_object_from_request()
        tweets = models.Tweet.gql('WHERE mine = :1 ORDER BY date DESC', mine).fetch(1000)
        self.template_values['tweets'] = simplejson.dumps([tweet.to_dict() for tweet in tweets])
        self.render('mine.html')

class HomePage(PageBase):
    def get(self):
        mines = models.Mine.gql('WHERE user = :1', self.google_user).fetch(10)
        self.template_values['mines'] = mines
        self.render('home.html')

class Xhr(XhrBase):
    def GetMines(self):
        mines = models.Mine.gql('WHERE user = :1', self.google_user).fetch(10)
        return {'mines':[mine.to_dict() for mine in mines]}
    
    def AddMine(self):
        key = models.Mine(user=self.google_user,
                          search=self.request.get('search')).put()
        tasks.MineTweets.fire(key=str(key))
        return self.GetMines()
    
    def DeleteMine(self):
        mine = db.get(self.request.get('key'))
        if mine:
            models.Mine.delete(mine)
        return self.GetMines()

class DeleteTweets(webapp.RequestHandler):
    def get(self):
        tweets = models.Tweet.all(keys_only=True).fetch(1000)
        db.delete(tweets)
        self.response.out.write('deleted %s' % len(tweets))

application = webapp.WSGIApplication(
                                     [
                                      ('/add_search', AddSearch),
                                      ('/remove_search', RemoveSearch),
                                      ('/mine/.*', TweetsPage),
                                      ('/deletetweets/.*', DeleteTweets),
                                      ('/xhr/.*', Xhr),
                                      ('/', HomePage),
                                      ], debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()