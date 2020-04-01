import re
import os
import json
import datetime
import pytest
import requests_mock
from unittest import mock
from bs4 import BeautifulSoup as Soup

from metafy.app import parse, URL, SpotifyAuth, Spotify


RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


# Spotify fixtures
@pytest.fixture
def RequestsMockedSpotifyAPI():
    with requests_mock.Mocker() as rm:
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/playlists/.*"),
                        json=json.load(open(os.path.join(RESOURCES, "tracks.json"))))
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/albums.*"),
                        json=json.load(open(os.path.join(RESOURCES, "albums.json"))))
        rm.register_uri("GET",
                        re.compile("https://api.spotify.com/v1/search.*"),
                        json=json.load(open(os.path.join(RESOURCES, "search.json"))))
        j = {"access_token": "YOURTOKEN", "expires_in": 3600}
        rm.register_uri("POST", "https://accounts.spotify.com/api/token", json=j)
        yield rm


@pytest.fixture
def AuthEnv(RequestsMockedSpotifyAPI):
    os.environ["SPOTIFY_CLIENT_ID"] = "client_id"
    os.environ["SPOTIFY_CLIENT_SECRET"] = "client_secret"
    os.environ["SPOTIFY_REF_TK"] = "ref_token"
    return SpotifyAuth(os.environ["SPOTIFY_CLIENT_ID"],
                       os.environ["SPOTIFY_CLIENT_SECRET"],
                       os.environ["SPOTIFY_REF_TK"])


@pytest.fixture
def MockedSpotifyAPI(AuthEnv, RequestsMockedSpotifyAPI):
    s = Spotify()
    yield s


# Metacritic Fixtures

@pytest.fixture
def MakeAlbum():
    def make(score, title, datestr, album):
        # must be two items so that it contains a list of results after parsing
        return f"""
          <div class="product_wrap">
            <div class="metascore_w">{score}</div>
            <div class="product_title"><a>{title}</a></div>
            <li class="release_date"><span class="data">{datestr}</span></li>
            <li class="product_artist"><span class="data">{album}</span></li>
          </div>
          <div class="product_wrap">
            <div class="metascore_w">{score}</div>
            <div class="product_title"><a>{title}</a></div>
            <li class="release_date"><span class="data">{datestr}</span></li>
            <li class="product_artist"><span class="data">{album}</span></li>
          </div>
        """
    return make


@pytest.fixture
def ScrapedAlbums():
    with open(os.path.join(RESOURCES, "metacritic_sample.html")) as f:
        yield parse(f.read())


@pytest.fixture
def MetacriticFailingMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", URL, text="failed to retrieve HTML", status_code=400)


@pytest.fixture
def MetacriticRateLimitMock():
    with requests_mock.Mocker() as m:
        m.register_uri("GET", URL, text="rate limited", status_code=429, headers={"Retry-After": "5"})