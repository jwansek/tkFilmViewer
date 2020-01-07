CREATE TABLE IF NOT EXISTS languages (
    language_id INTEGER PRIMARY KEY,
    iso_639_1 TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS films (
    film_id INTEGER PRIMARY KEY,
    tmdb_id INTEGER NOT NULL,
    imdb_id TEXT NOT NULL,
    path TEXT NOT NULL,
    original_name TEXT NOT NULL,
    name TEXT NOT NULL,
    release TEXT NOT NULL,
    overview TEXT NULL,
    original_language INTEGER NOT NULL,
    budget INTEGER NULL,
    revenue INTEGER NULL,
    backdrop_img TEXT NULL,
    poster_img TEXT NULL,
    runtime INT NOT NULL,
    score DECIMAL(1,1) NOT NULL,
    url TEXT NULL,
    FOREIGN KEY (original_language) REFERENCES languages(language_id)
);

CREATE TABLE IF NOT EXISTS castmembers (
    castmember_id INTEGER PRIMARY KEY,
    character TEXT NOT NULL,
    name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    img TEXT NULL,
    film_id INTEGER NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id)
);

CREATE TABLE IF NOT EXISTS crewmembers (
    crewmember_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    job TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    img TEXT NULL,
    film_id INTEGER NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id)
);

CREATE TABLE IF NOT EXISTS countries (
    country_id INTEGER PRIMARY KEY,
    iso_3166_1 TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    tmdb_id INTEGER NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS production_countries (
    production_country_id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL,
    film_id INTEGER NOT NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id),
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE IF NOT EXISTS spoken_languages (
    spoken_language_id INTEGER PRIMARY KEY,
    language_id INTEGER NOT NULL,
    film_id INTEGER NOT NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id)
);

CREATE TABLE IF NOT EXISTS media_genres (
    media_genres_id INTEGER PRIMARY KEY,
    genre_id INTEGER NOT NULL,
    film_id INTEGER NOT NULL,
    FOREIGN KEY (film_id) REFERENCES films(film_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);