import re
import os
import json
from typing import Any, Dict, Generator, AsyncIterator
import scrapy
from scrapy import Request, Spider
from scrapy.utils.project import get_project_settings

class TMDBSpider(Spider):
    name = "tmdb"
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print("DEBUG SPIDER: __init__ called")
        # Load API key from environment variable or scrapy settings
        self.api_key = os.getenv("TMDB_API_KEY") or get_project_settings().get("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        print(f"DEBUG SPIDER: base_url is {self.base_url}, api_key exists: {bool(self.api_key)}")

    async def start(self) -> AsyncIterator[Request]:
        self.logger.info(f"start_called: API key is present: {bool(self.api_key)}")
        if not self.api_key:
            self.logger.warning("TMDB_API_KEY environment variable not set. Falling back to mock movie generator.")
            yield Request(url="https://httpbin.org/get", callback=self.parse_mock)
            return

        url = f"{self.base_url}/movie/now_playing?api_key={self.api_key}&region=IN&page=1"
        self.logger.info(f"Yielding live request to: {self.base_url}/movie/now_playing")
        yield Request(url=url, callback=self.parse_now_playing)

    def parse_mock(self, response) -> Generator[Dict[str, Any], None, None]:
        yield from self.generate_mock_movies()

    def parse_now_playing(self, response) -> Generator[Request, None, None]:
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse TMDB now_playing JSON response.")
            return

        results = data.get("results", [])
        for movie in results[:10]:
            movie_id = movie.get("id")
            if movie_id:
                detail_url = f"{self.base_url}/movie/{movie_id}?api_key={self.api_key}&append_to_response=credits,videos"
                yield Request(url=detail_url, callback=self.parse_movie_details)

    def parse_movie_details(self, response) -> Generator[Dict[str, Any], None, None]:
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse details for movie response: {response.url}")
            return

        title = data.get("title")
        if not title:
            return

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        
        genres = [g.get("name") for g in data.get("genres", []) if g.get("name")]
        
        trailer_url = None
        videos = data.get("videos", {}).get("results", [])
        for video in videos:
            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break

        cast = []
        for cast_member in data.get("credits", {}).get("cast", [])[:5]:
            cast.append({
                "name": cast_member.get("name"),
                "role": "Actor"
            })

        crew = []
        crew_members = data.get("credits", {}).get("crew", [])
        for member in crew_members:
            job = member.get("job")
            if job in ("Director", "Producer", "Composer"):
                crew.append({
                    "name": member.get("name"),
                    "role": job
                })

        rating = "A" if data.get("adult") else "UA"

        poster_path = data.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        backdrop_path = data.get("backdrop_path")
        banner_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else None

        yield {
            "title": title,
            "slug": slug,
            "synopsis": data.get("overview"),
            "language": data.get("original_language", "en").upper(),
            "genre": genres or ["Drama"],
            "duration_minutes": data.get("runtime") or 120,
            "rating": rating,
            "release_date": data.get("release_date"),
            "poster_url": poster_url,
            "banner_url": banner_url,
            "trailer_url": trailer_url,
            "cast": [c["name"] for c in cast],
            "crew": {c["role"].lower(): c["name"] for c in crew}
        }

    def generate_mock_movies(self) -> Generator[Dict[str, Any], None, None]:
        # High quality fallback dataset
        mock_data = [
            {
                "title": "Interstellar",
                "slug": "interstellar",
                "synopsis": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                "language": "EN",
                "genre": ["Sci-Fi", "Adventure", "Drama"],
                "duration_minutes": 169,
                "rating": "UA",
                "release_date": "2014-11-07",
                "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NIvHG3Rmd5xtxtR.jpg",
                "banner_url": "https://image.tmdb.org/t/p/original/xJHok70jZZyJ69tH6VTGuarC8zs.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=zSWdZAIBEsA",
                "cast": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain", "Michael Caine"],
                "crew": {"director": "Christopher Nolan", "composer": "Hans Zimmer"}
            },
            {
                "title": "Inception",
                "slug": "inception",
                "synopsis": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea.",
                "language": "EN",
                "genre": ["Action", "Sci-Fi", "Adventure"],
                "duration_minutes": 148,
                "rating": "UA",
                "release_date": "2010-07-16",
                "poster_url": "https://image.tmdb.org/t/p/w500/o0j4TCuP1v2iT1uQj95j95STvya.jpg",
                "banner_url": "https://image.tmdb.org/t/p/original/s3Tzczdf3UHld4BF8HYYr7jY8G5.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
                "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page", "Tom Hardy"],
                "crew": {"director": "Christopher Nolan", "composer": "Hans Zimmer"}
            },
            {
                "title": "The Dark Knight",
                "slug": "the-dark-knight",
                "synopsis": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests.",
                "language": "EN",
                "genre": ["Action", "Crime", "Drama"],
                "duration_minutes": 152,
                "rating": "UA",
                "release_date": "2008-07-18",
                "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tWGB2ez9jCwqVj54n37188uN.jpg",
                "banner_url": "https://image.tmdb.org/t/p/original/nMKdUUueJZ57qtjT6hR1w4z6ldM.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
                "cast": ["Christian Bale", "Heath Ledger", "Aaron Eckhart", "Maggie Gyllenhaal"],
                "crew": {"director": "Christopher Nolan", "composer": "Hans Zimmer"}
            }
        ]
        for item in mock_data:
            yield item
