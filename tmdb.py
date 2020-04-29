import urllib3
import requests
import PIL
import database
import files
import json
import os

with open("settings.json", "r") as f:
    settings = json.load(f)

APIKEY = settings["apikey"]
LANGUAGE = settings["language"]
DBPATH = os.path.join(*settings["dbpath"].split("/"))
MEDIA_PATHS = settings["media_paths"]
EXTENSION_BLACKLIST = settings["extension_blacklist"]
FFPROBE_LOCATION = settings["ffprobe_location"]
IMG_PATH = os.path.join(*settings["imgpath"].split("/"))
IMG_PREFIX = settings["img_prefix"]

APICALLS = 0

class TMDBRequest:
    def __init__(self, url):
        global APICALLS
        APICALLS += 1
        self.response = requests.get(url)
        if self.response.status_code == 200:
            self.decoded = json.loads(self.response.content.decode())
        else:
            raise TMDBRequestException(self.response)
    
    def get_results(self):
        return self.decoded["results"]

class TMDBRequestException(Exception):
    pass

#TODO: use a recursive generator with `pages` to get more than 20 results
def search(title, year = None, maxresults = 10):
    if year is None:
        searchingfor = "tv"
        url = "https://api.themoviedb.org/3/search/tv?api_key=%s&language=%s&query=%s&page=1&include_adult=false" % (APIKEY, LANGUAGE, title)
    else:
        searchingfor = "movie"
        url = "https://api.themoviedb.org/3/search/movie?api_key=%s&language=%s&query=%s&page=1&include_adult=false&year=%i" % (APIKEY, LANGUAGE, title, year)

    request = TMDBRequest(url)
    results = request.get_results()
    for i, result in enumerate(results, 0):
        if maxresults is not None and i >= maxresults:
            break
        url = "https://api.themoviedb.org/3/%s/%s?api_key=%s&language=%s" % (searchingfor, result["id"], APIKEY, LANGUAGE)
        mediadata = TMDBRequest(url)
        url = "https://api.themoviedb.org/3/%s/%s/credits?api_key=%s" % (searchingfor, result["id"], APIKEY)
        creditsdata = TMDBRequest(url)
        yield {"data": mediadata.decoded, "cast":creditsdata.decoded["cast"], "crew":creditsdata.decoded["crew"]}

def getEpisodes(tv_id, season_id, episodes):
    out = []
    for episode in range(1, episodes + 1):
        url = "https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s?api_key=%s&language=%s" % (tv_id, season_id, episode, APIKEY, LANGUAGE)
        request = TMDBRequest(url)
        out.append(request.decoded)
    return out
        
def searchOne(title, year = None):
    return next(search(title, year))

if __name__ == "__main__":
    # print(searchOne("Line of Duty")["data"]["id"])
    print(getEpisodes("43982", 1, 5))
