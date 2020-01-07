import subprocess
import tmdb
import json
import os

def find_film(path):
    if "(" in os.path.split(path)[-1]:
        for root, dirs, files in os.walk(path):
            for file in files:
                videopath = os.path.join(root, file)
                if os.path.splitext(videopath)[-1] not in tmdb.EXTENSION_BLACKLIST:
                    try:
                        print(videopath)
                        md = Metadata(videopath)
                        print(md.get_frames())
                        print(md.get_fps())
                        print()
                    except MetadataException:
                        pass

class Metadata:
    def __init__(self, path):
        self.path = path

    def _probe(self, args):
        proc = subprocess.Popen(["ffprobe", "-v", "error"] + args + ["-print_format", "json", self.path], stdout=subprocess.PIPE)
        jsonout = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            jsonout += line.rstrip().decode()

        return json.loads(jsonout)

    def get_all(self):
        return self._probe(args = ["-show_streams"])

    def get_frames(self):
        return self._probe(args = ["-show_entries", "format=duration"])["format"]

    def get_fps(self):
        try:
            fraction = self._probe(args = ["-select_streams", "v", "-show_entries", "stream=r_frame_rate"])["streams"][0]["r_frame_rate"]
            s = fraction.split("/")
            return int(s[0]) / int(s[1])
        except IndexError:
            raise MetadataException("Couldn't extract FPS for %s" % self.path)

class MetadataException(Exception):
    pass


if __name__ == "__main__":
    # get_file_metadata("/media/veracrypt2/Videos/War Games (1983)/War Games [1983] =25th Anniversary Edition=.mkv")
    get_file_metadata("tmdb.py")
