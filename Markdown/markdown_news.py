import urllib.request
import json

NEWS_URL = 'https://BUCKER-NAME.s3.REGION.amazonaws.com/news.json'

# Download news from URL using urlib2
def download_news(news_url):
    return urllib.request.urlopen(news_url).read()

def print_news(news):
    print("# {}\n".format(news['title']))
    for n in news:
        print("## [{}]({})\n".format(n['title'], n['link']))
        print("{}\n".format(n['summary']))

if __name__=='__main__':
    news = json.loads(download_news(NEWS_URL))
    print_news(news)