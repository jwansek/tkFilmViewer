import database
import sqlite3
import tmdb
import os
import re

class Database:
    def __init__(self):
        if not os.path.exists(tmdb.DBPATH):
            self._create_db()
        else:
            self.connection = sqlite3.connect(tmdb.DBPATH)
            self.cursor = self.connection.cursor()

    def _create_db(self):
        dirs, name = os.path.split(tmdb.DBPATH)
        os.makedirs(dirs, exist_ok=True)
        self.connection = sqlite3.connect(tmdb.DBPATH)
        self.cursor = self.connection.cursor()
        with open("create_tables.sql", "r") as script:
            self.cursor.executescript(script.read())
        self.connection.commit()

    def add_film(self, path, data):
        #get genre ids, creating them if they don't exist
        genreids = []
        for genre in data["data"]["genres"]:
            self.cursor.execute("SELECT genre_id FROM genres WHERE name = ?", (genre["name"], ))
            try:
                genreids.append(self.cursor.fetchone()[0])
            except TypeError:
                self.cursor.execute("INSERT INTO genres (tmdb_id, name) VALUES (?, ?)", (genre["id"], genre["name"]))
                self.connection.commit()
                self.cursor.execute("SELECT genre_id FROM genres WHERE name = ?", (genre["name"], ))
                genreids.append(self.cursor.fetchone()[0])

        #get language ids, creating them if they don't exist
        languageids = []
        for language in data["data"]["spoken_languages"]:
            self.cursor.execute("SELECT language_id FROM languages WHERE iso_639_1 = ?", (language["iso_639_1"], ))
            try:
                languageids.append(self.cursor.fetchone()[0])
            except TypeError:
                self.cursor.execute("INSERT INTO languages (iso_639_1, name) VALUES (?, ?)", (language["iso_639_1"], language["name"]))
                self.connection.commit()
                self.cursor.execute("SELECT language_id FROM languages WHERE iso_639_1 = ?", (language["iso_639_1"], ))
                languageids.append(self.cursor.fetchone()[0])

        #get country ids, creating them if they don't exist
        countryids = []
        for country in data["data"]["production_countries"]:
            self.cursor.execute("SELECT country_id FROM countries WHERE iso_3166_1 = ?", (country["iso_3166_1"], ))
            try:
                countryids.append(self.cursor.fetchone()[0])
            except TypeError:
                self.cursor.execute("INSERT INTO countries (iso_3166_1, name) VALUES (?, ?)", (country["iso_3166_1"], country["name"]))
                self.connection.commit()
                self.cursor.execute("SELECT country_id FROM countries WHERE iso_3166_1 = ?", (country["iso_3166_1"], ))
                countryids.append(self.cursor.fetchone()[0])

        #we assume that the language has just been added, and then we get the original language id
        self.cursor.execute("SELECT language_id FROM languages WHERE iso_639_1 = ?", (data["data"]["original_language"], ))
        origlangid = self.cursor.fetchone()[0]

        #the big one, add the film
        self.cursor.execute("""
        INSERT INTO films (
            tmdb_id, imdb_id, path, original_name,
            name, release, overview, original_language,
            budget, revenue, backdrop_img, poster_img,
            runtime, score, url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data["data"]["id"], data["data"]["imdb_id"], path, data["data"]["original_title"],
            data["data"]["title"], data["data"]["release_date"], data["data"]["overview"], origlangid,
            data["data"]["budget"], data["data"]["revenue"], data["data"]["backdrop_path"], data["data"]["poster_path"],
            data["data"]["runtime"], data["data"]["vote_average"], data["data"]["homepage"]
        ))
        #get the new film id
        self.connection.commit()
        self.cursor.execute("SELECT film_id FROM films WHERE path = ?", (path, ))
        newid = self.cursor.fetchone()[0]

        #add cast and crew to their respective databases
        castinfo = [[c["character"], c["name"], c["order"], c["profile_path"], newid] for c in data["cast"]]
        crewinfo = [[c["name"], c["job"], i, c["profile_path"], newid] for i, c in enumerate(data["crew"], 0)]
        self.cursor.executemany("""
        INSERT INTO castmembers (character, name, display_order, img, film_id)
        VALUES (?, ?, ?, ?, ?);""", castinfo)
        self.cursor.executemany("""
        INSERT INTO crewmembers (name, job, display_order, img, film_id)
        VALUES (?, ?, ?, ?, ?);""", crewinfo)

        #add production countries, genres and spoken languages to linker tables
        countryinfo = [[c, newid] for c in countryids]
        languageinfo = [[c, newid] for c in languageids]
        genreinfo = [[c, newid] for c in genreids]
        self.cursor.executemany("""
        INSERT INTO production_countries (country_id, film_id)
        VALUES (?, ?)""", countryinfo)
        self.cursor.executemany("""
        INSERT INTO spoken_languages (language_id, film_id)
        VALUES (?, ?)""", languageinfo)
        self.cursor.executemany("""
        INSERT INTO media_genres (genre_id, film_id)
        VALUES (?, ?)""", genreinfo)

        self.connection.commit()

    def get_all_paths(self):
        self.cursor.execute("SELECT path FROM films;")
        return [i[0] for i in self.cursor.fetchall()]

    def compare_paths(self, mediadata):
        dbpaths = {os.path.split(i[0])[:-1][0] for i in self.get_all_paths() if os.path.split(i[0])[:-1][0] != ""}
        return list(set(mediadata) - dbpaths)
        
    def get_poster_img(self, path):
        self.cursor.execute("SELECT poster_img FROM films WHERE path = ?", (path, ))
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return None

    def get_film(self, filepath):
        self.cursor.execute("SELECT * FROM films WHERE path = ?;", (filepath, ))
        try:
            sqlout = self.cursor.fetchall()[0]
        except TypeError:
            title, year = files.extract_film_name_year(filepath)
            self.add_film(filepath, tmdb.searchOneFilm(title, year))
            return self.get_film(filepath)

        else:
            # self.cursor.execute("SELECT sql FROM sqlite_master WHERE tbl_name = 'films' AND type = 'table';")
            # fieldnames = [i.split()[0] for i in self.cursor.fetchall()[0][0].split("\n")[1:-2]]
            fieldnames = ['film_id', 'tmdb_id', 'imdb_id', 'path', 'original_name', 'name', 'release', 'overview', 'original_language', 'budget', 'revenue', 'backdrop_img', 'poster_img', 'runtime', 'score', 'url']
            out = {}
            for i in range(len(sqlout)):
                out[fieldnames[i]] = sqlout[i]
            self.cursor.execute("SELECT character, name, img FROM castmembers WHERE film_id = ? ORDER BY display_order;", (out["film_id"], ))
            out["cast"] = self.cursor.fetchall()
            self.cursor.execute("SELECT name, job, img FROM crewmembers WHERE film_id = ? ORDER BY display_order;", (out["film_id"], ))
            out["crew"] = self.cursor.fetchall()
            self.cursor.execute("SELECT iso_3166_1, name FROM production_countries INNER JOIN countries ON countries.country_id = production_countries.country_id WHERE film_id = ?;", (out["film_id"], ))
            out["production_countries"] = self.cursor.fetchall()
            self.cursor.execute("SELECT tmdb_id, name FROM media_genres INNER JOIN genres ON genres.genre_id = media_genres.genre_id WHERE film_id = ?;", (out["film_id"], ))
            return out
            self.cursor.execute("SELECT iso_639_1, name FROM spoken_languages INNER JOIN languages ON languages.language_id = spoken_languages.language_id WHERE film_id = ?;", (out["film_id"], ))
            out["spoken_languages"] = self.cursor.fetchall()
            return out


if __name__ == "__main__":
    # import subprocess
    # subprocess.run(["rm", "-r", "tmdbcache/"])
    db = Database()
    print(db.get_film(r"V:\Videos\12 Years a Slave (2013) [1080p]\12.Years.a.Slave.2013.1080p.BluRay.x264.YIFY.mp4"))