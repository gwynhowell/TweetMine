from datetime import datetime
from django.utils import simplejson
from google.appengine.api import urlfetch, taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import os
import rfc822

SEARCH_URL = 'http://search.twitter.com/search.json'

class Search(db.Model):
    search = db.StringProperty()
    url = db.StringProperty()

class Tweet(db.Model):
    search = db.ReferenceProperty(reference_class=Search, collection_name='tweets')
    id = db.StringProperty()
    text = db.TextProperty()
    date = db.DateTimeProperty()
    created = db.DateTimeProperty(auto_now_add=True)


class AddSearch(webapp.RequestHandler):
    def get(self):
        search = self.request.get('search')
        Search(search=search).put()
        self.response.out.write('Added ' + search)
        
class RemoveSearch(webapp.RequestHandler):
    def get(self):
        search = self.request.get('search')
        stuff = Search.gql('WHERE search = :1', search).fetch(100)
        if stuff:
            db.delete(stuff)
        self.response.out.write('Deleted ' + search)

class CronHandler(webapp.RequestHandler):
    def post(self):
        searches = Search.all().fetch(100)
        for s in searches:
            taskqueue.add(url='/get_tweets', params={'key':str(s.key())})

class GetTweets(webapp.RequestHandler):
    def get(self):
        searches = Search.all().fetch(100)
        for s in searches:
            taskqueue.add(url='/get_tweets', params={'key':str(s.key())})
        
    def post(self):
        #db.delete(Tweet.all())
        search = Search.get(self.request.get('key'))

        #last_tweet = Tweet.gql('WHERE ANCESTOR IS :1 ORDER BY date DESC', search).get()
        #url = 'http://search.twitter.com/search.json?q=' + search
        #if last_tweet:
        #    url += '&since_id=' + last_tweet.id
        
        url = SEARCH_URL
        url += search.url if search.url else '?q=' + search.search
        url += '&rpp=100'
        r = urlfetch.fetch(url)
        if r.status_code == 200:
            twitter_resp = simplejson.loads(r.content)
            
            if not twitter_resp['results']:
                return
            
            for result in twitter_resp['results']:
                created = datetime(*rfc822.parsedate(result['created_at'])[:7])
                Tweet(parent=search,
                      search=search,
                      id=result['id_str'],
                      text=result['text'],
                      date=created).put()
            
            search.url = twitter_resp['refresh_url']
            search.put()
            
            taskqueue.add(url='/get_tweets', params={'key':str(search.key())})
    
class TweetsPage(webapp.RequestHandler):
    def get(self):
        searches = Search.all().fetch(100)
        dir_name = os.path.dirname(__file__)
        template_path = os.path.join(dir_name, 'tweets.html')
        self.response.out.write(template.render(template_path, {'searches':searches}))
    
application = webapp.WSGIApplication(
                                     [
                                      ('/get_tweets', GetTweets),
                                      ('/add_search', AddSearch),
                                      ('/remove_search', RemoveSearch),
                                      ('/tweets', TweetsPage),
                                      ('/cron', CronHandler),
                                      ], debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()