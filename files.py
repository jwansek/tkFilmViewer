import subprocess
import platform
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

class MetadataException(Exception):
    pass

