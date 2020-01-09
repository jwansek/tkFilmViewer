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
    
    def get_results(self):
        return self.decoded["results"]

class TMDBRequestException(Exception):
    pass

#TODO: use a recursive generator with `pages` to get more than 20 results
def filmSearch(title, year, maxresults = None):
    url = "https://api.themoviedb.org/3/search/movie?api_key=%s&language=%s&query=%s&page=1&include_adult=false&year=%i" % (APIKEY, LANGUAGE, title, year)
    request = TMDBRequest(url)
    results = request.get_results()
    for i, result in enumerate(results, 0):
        if maxresults is not None and i >= maxresults:
            break
        url = "https://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s" % (result["id"], APIKEY, LANGUAGE)
        filmdata = TMDBRequest(url)
        url = "https://api.themoviedb.org/3/movie/%s/credits?api_key=%s" % (result["id"], APIKEY)
        creditsdata = TMDBRequest(url)
        yield {"data": filmdata.decoded, "cast":creditsdata.decoded["cast"], "crew":creditsdata.decoded["crew"]}

def searchOneFilm(title, year):
    # return [x for _, x in zip(range(1), filmSearch(title, year))][0]
    return next(filmSearch(title, year))

if __name__ == "__main__":
    # db = database.Database()
    # for path in MEDIA_PATHS:
    #     if os.path.exists(path):
    #         for dir_ in os.listdir(path):
    #             if "(" in os.path.split(dir_)[-1]:
    #                 s = os.path.split(dir_)[-1].split("(")
    #                 title = s[0]
    #                 year = int(s[1][:4])
    #                 filmfile = files.find_film(os.path.join(path, dir_))
    #                 db.add_film(filmfile, searchOneFilm(title, year))
    #                 print(title, year)

    print(searchOneFilm("1984", 1984))

    print("\n\n", APICALLS, "API calls")