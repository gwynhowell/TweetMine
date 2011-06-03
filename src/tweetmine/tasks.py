from django.utils import simplejson
from google.appengine.api import taskqueue, urlfetch, memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from datetime import datetime
import models
import rfc822

SEARCH_URL = 'http://search.twitter.com/search.json'

class MineTweets(webapp.RequestHandler):
    @staticmethod
    def fire(**params):
        taskqueue.add(url='/tasks/mine', params=params)
    
    def get(self):
        mines = models.Mine.all().fetch(1000)
        for mine in mines:
            MineTweets.fire(key=str(mine.key()))
        
    def post(self):
        #db.delete(Tweet.all())
        key = self.request.get('key')
        mine = models.Mine.get(key)

        #last_tweet = Tweet.gql('WHERE ANCESTOR IS :1 ORDER BY date DESC', search).get()
        #url = 'http://search.twitter.com/search.json?q=' + search
        #if last_tweet:
        #    url += '&since_id=' + last_tweet.id
        
        cache = memcache.Client()
        
        url = SEARCH_URL
        url += mine.url if mine.url else '?q=' + mine.search
        url += '&rpp=100'
        r = urlfetch.fetch(url)
        if r.status_code == 200:
            twitter_resp = simplejson.loads(r.content)
            
            if not twitter_resp['results']:
                self.dump_count(cache, mine)
                return

            mine.url = twitter_resp['refresh_url']
            mine.put()
            
            MineTweets.fire(key=key)
            
            for result in twitter_resp['results']:
                created = datetime(*rfc822.parsedate(result['created_at'])[:7])
                models.Tweet(parent=mine,
                             mine=mine,
                             id=result['id_str'],
                             text=result['text'],
                             date=created).put()
                cache.incr(key, initial_value=mine.count)
            self.dump_count(cache, mine)

    def dump_count(self, cache, mine):
        count = cache.get(str(mine.key()))
        if count:
            mine.count = int(count)
            mine.put()

application = webapp.WSGIApplication(
                                     [
                                      ('/tasks/mine', MineTweets),
                                      ], debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()