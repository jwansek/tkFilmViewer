from PIL import Image
import subprocess
import platform
import urllib
import tmdb
import json
import os

def find_film(path):
    """Gets the full path of the film file in a folder.
    Works by getting the video file with the most frames in it.
    
    Arguments:
        path {str} -- path to the directory to check
    
    Returns:
        str -- full path of the film
    """
    longestfile = [None, 0]
    for root, dirs, files in os.walk(path):
        for file in files:
            videopath = os.path.join(root, file)
            if os.path.splitext(videopath)[-1] not in tmdb.EXTENSION_BLACKLIST:
                try:
                    md = Metadata(videopath)
                    len_ = len(md)
                    if len_ > longestfile[1]:
                        longestfile = [videopath, len_]
                except MetadataException:
                    pass

    return longestfile[0]

class Metadata:
    def __init__(self, path):
        self.path = path

        if platform.system() != "Windows":
            self._ffprobe = "ffprobe"
        else:
            self._ffprobe = tmdb.FFPROBE_LOCATION

    def _probe(self, args):
        proc = subprocess.Popen([self._ffprobe, "-v", "error"] + args + ["-print_format", "json", self.path], stdout=subprocess.PIPE)
        jsonout = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            jsonout += line.rstrip().decode()

        return json.loads(jsonout)

    def get_all(self):
        return self._probe(args = ["-show_streams"])

    def __len__(self):
        try:
            return int(float(self._probe(args = ["-show_entries", "format=duration"])["format"]["duration"]))
        except KeyError as e:
            raise MetadataException("Couldn't get the length for %s" % self.path)

    def get_fps(self):
        try:
            fraction = self._probe(args = ["-select_streams", "v", "-show_entries", "stream=r_frame_rate"])["streams"][0]["r_frame_rate"]
            s = fraction.split("/")
            return int(s[0]) / int(s[1])
        except IndexError:
            raise MetadataException("Couldn't extract FPS for %s" % self.path)

def _download_img(name):
    req = urllib.request.Request(tmdb.IMG_PREFIX + name, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/534.50.2 (KHTML, like Gecko) Version/5.0.6 Safari/533.22.3'})
    mediaContent = urllib.request.urlopen(req).read()
    with open(os.path.join(tmdb.IMG_PATH, name), "wb") as f:
        f.write(mediaContent)

def get_image(name):
    os.makedirs(tmdb.IMG_PATH, exist_ok=True)
    if name.startswith("/"):
        name = name[1:]
    if name not in os.listdir(tmdb.IMG_PATH):
        _download_img(name)

    return Image.open(os.path.join(tmdb.IMG_PATH, name))

def resize(img, **kwargs):
    """Resizes an Image, maintaining the height to width
    ratio when given a named argument height or width.
    
    Arguments:
        img {Image} -- Source image
    
    Raises:
        TypeError -- Thrown if the keyword argument 'height'
        or 'width' is not found.
    
    Returns:
        Image -- resized image
    """

    if list(kwargs.keys())[0] == 'height':
        baseheight = kwargs['height']
        hpercent = baseheight / float(img.size[1])
        wsize = int(float(img.size[0]) * float(hpercent))
        return img.resize((wsize, baseheight), Image.ANTIALIAS)
    elif list(kwargs.keys())[0] == 'width':
        basewidth = kwargs['width']
        wpercent = basewidth / float(img.size[0])
        hsize = int(float(img.size[1]) * float(wpercent))
        return img.resize((basewidth, hsize), Image.ANTIALIAS)
    raise TypeError("Missing argument: must have 'height' or 'width'.")

def get_all_films():
    films = []
    for path in tmdb.MEDIA_PATHS:
        if os.path.exists(path):
            for dir_ in os.listdir(path):
                if "(" in os.path.split(dir_)[-1]:
                    films.append(os.path.join(path, dir_))

    return films

def extract_film_name_year(path):
    s = os.path.split(path)[-1].split("(")
    return s[0][:-1], int(s[1][:4])

class MetadataException(Exception):
    pass

if __name__ == "__main__":
    # get_image("/upgi8oTlMthM9sweAyBoXqr8doZ.jpg")
    print(extract_film_name_year("/media/veracrypt2/Videos/The Pianist (2002) [1080p]/The.Pianist.2002.1080p.BrRip.x264.YIFY.mp4"))
    print(extract_film_name_year("/media/veracrypt2/Videos/War and Peace (1967) [1080p]/Part 1/War and Peace (Война и мир) (HD) Part 1-1- Andrei Bolkonsky.mkv"))

