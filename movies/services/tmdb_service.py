import logging
from datetime import datetime
from typing import Any
import re
import unicodedata

import requests
from django.conf import settings
from django.utils import timezone

from movies.models import Movie


logger = logging.getLogger(__name__)

TMDB_API_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

REQUEST_TIMEOUT = 15


class TMDbError(Exception):
    """Raised when a TMDb request or movie match fails."""


def tmdb_request(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Send one authenticated request to TMDb.

    The API key is read from settings.py, which reads it from .env.
    """

    request_params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "en-US",
    }

    if params:
        request_params.update(params)

    url = f"{TMDB_API_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(
            url,
            params=request_params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise TMDbError(
            f"TMDb request failed: {error}"
        ) from error

    return response.json()


def normalize_title(title: str) -> str:
    """
    Normalize movie titles so punctuation and capitalization
    do not prevent valid TMDb matches.

    Examples:
    "John Wick: Chapter 4"
    "John Wick Chapter 4"

    Both become:
    "john wick chapter 4"
    """

    if not title:
        return ""

    # Convert accented characters into comparable plain text.
    title = unicodedata.normalize("NFKD", title)

    # Make everything lowercase.
    title = title.lower()

    # Replace ampersands with the word "and".
    title = title.replace("&", " and ")

    # Remove punctuation such as :, -, ', and parentheses.
    title = re.sub(r"[^a-z0-9\s]", " ", title)

    # Remove duplicate spaces.
    title = " ".join(title.split())

    return title

def clean_tmdb_search_title(title: str) -> str:
    """
    Remove media-storage labels that are not normally part
    of an official movie title.

    Examples:

    "Glory Disc 1" becomes "Glory"
    "The Last Don Part 2" becomes "The Last Don"
    "Movie Name DVD 1" becomes "Movie Name"

    This changes only the title sent to TMDb.
    It does not rename the movie in the database.
    """

    if not title:
        return ""

    cleaned_title = title.strip()

    removable_patterns = [
        r"\s+disc\s*\d+$",
        r"\s+disk\s*\d+$",
        r"\s+dvd\s*\d+$",
        r"\s+blu[\s-]*ray\s*\d+$",
        r"\s+part\s*\d+$",
    ]

    for pattern in removable_patterns:
        cleaned_title = re.sub(
            pattern,
            "",
            cleaned_title,
            flags=re.IGNORECASE,
        ).strip()

    return cleaned_title


def extract_year(date_string: str | None) -> int | None:
    """
    Convert a TMDb date such as 2024-08-16 into the year 2024.
    """

    if not date_string:
        return None

    try:
        return datetime.strptime(
            date_string,
            "%Y-%m-%d",
        ).year

    except ValueError:
        return None


def find_best_movie_match(
    title: str,
    release_year: int | None = None,
) -> dict[str, Any]:
    """
    Search TMDb and select the safest movie match.

    Matching order:
    1. Exact normalized title and exact year.
    2. Exact normalized title with a nearby year.
    3. Partial title match with an exact year.
    4. Partial title match with a nearby year.
    """

    search_title = clean_tmdb_search_title(title)

    search_params = {
        "query": search_title,
        "include_adult": "false",
    }

    if release_year:
        search_params["primary_release_year"] = release_year

    search_data = tmdb_request(
    "search/movie",
    params={
        "query": search_title,
        "include_adult": "false",
    },
)

    results = search_data.get("results", [])

    # Retry without the year because some movies have different
    # theatrical, international, or digital release years.
    if not results and release_year:
        search_data = tmdb_request(
            "search/movie",
            params={
                "query": title,
                "include_adult": "false",
            },
        )

        results = search_data.get("results", [])

    if not results:
        raise TMDbError(
            f'No TMDb results found for "{title}".'
        )

    requested_title = normalize_title(search_title)

    exact_matches = []
    partial_matches = []

    for result in results:
        tmdb_title = normalize_title(
            result.get("title", "")
        )

        original_title = normalize_title(
            result.get("original_title", "")
        )

        available_titles = {
            tmdb_title,
            original_title,
        }

        # Exact match after punctuation has been removed.
        if requested_title in available_titles:
            exact_matches.append(result)
            continue

        # Allow one normalized title to contain the other.
        # This handles titles such as:
        # "X-Men United" versus "X2 X-Men United".
        partial_match = any(
            requested_title in candidate
            or candidate in requested_title
            for candidate in available_titles
            if candidate
        )

        if partial_match:
            partial_matches.append(result)

    # Best option: exact normalized title and exact year.
    if release_year:
        for result in exact_matches:
            result_year = extract_year(
                result.get("release_date")
            )

            if result_year == release_year:
                return result

    # Exact normalized title with the closest release year.
    if exact_matches:
        if release_year:
            return min(
                exact_matches,
                key=lambda result: abs(
                    (
                        extract_year(
                            result.get("release_date")
                        )
                        or release_year
                    )
                    - release_year
                ),
            )

        return exact_matches[0]

    # Partial title match with exact year.
    if release_year:
        for result in partial_matches:
            result_year = extract_year(
                result.get("release_date")
            )

            if result_year == release_year:
                return result

    # Partial title match with nearby year.
    if partial_matches:
        if release_year:
            closest_match = min(
                partial_matches,
                key=lambda result: abs(
                    (
                        extract_year(
                            result.get("release_date")
                        )
                        or release_year
                    )
                    - release_year
                ),
            )

            closest_year = extract_year(
                closest_match.get("release_date")
            )

            # Only accept a partial match if the release year is
            # no more than one year away.
            if (
                closest_year is not None
                and abs(closest_year - release_year) <= 1
            ):
                return closest_match

        # Without a year, partial matches are not safe enough.
        raise TMDbError(
            f'Partial title matches found for "{title}", '
            "but none could be verified by release year."
        )

    raise TMDbError(
        f'No confident title match found for "{title}".'
    )


def get_us_certification(
    release_dates: dict[str, Any],
) -> str:
    """
    Read the US movie certification from TMDb release-date data.

    Preference:
    1. Theatrical release
    2. Theatrical limited release
    3. Digital/physical release
    4. Any available US certification
    """

    preferred_types = [3, 2, 4, 5, 6, 1]

    us_entries = next(
        (
            country
            for country in release_dates.get("results", [])
            if country.get("iso_3166_1") == "US"
        ),
        None,
    )

    if not us_entries:
        return ""

    releases = us_entries.get("release_dates", [])

    for release_type in preferred_types:
        for release in releases:
            certification = release.get(
                "certification",
                ""
            ).strip()

            if (
                release.get("type") == release_type
                and certification
            ):
                return certification

    return ""


def build_movie_metadata(
    movie: Movie,
) -> dict[str, Any]:
    """
    Search TMDb and build the fields that will be saved locally.
    """

    match = find_best_movie_match(
        title=movie.title,
        release_year=movie.release_year,
    )

    tmdb_id = match["id"]

    # append_to_response lets one request include credits,
    # release dates, and external identifiers.
    details = tmdb_request(
        f"movie/{tmdb_id}",
        params={
            "append_to_response":
                "credits,release_dates,external_ids"
        },
    )

    credits = details.get("credits", {})

    cast_members = credits.get("cast", [])[:8]

    cast_names = [
        person["name"]
        for person in cast_members
        if person.get("name")
    ]

    directors = [
        person["name"]
        for person in credits.get("crew", [])
        if (
            person.get("job") == "Director"
            and person.get("name")
        )
    ]

    genres = [
        genre["name"]
        for genre in details.get("genres", [])
        if genre.get("name")
    ]

    studios = [
        company["name"]
        for company in details.get(
            "production_companies",
            [],
        )[:3]
        if company.get("name")
    ]

    collection_data = details.get(
        "belongs_to_collection"
    )

    collection_name = ""

    if collection_data:
        collection_name = collection_data.get(
            "name",
            "",
        )

    release_year = extract_year(
        details.get("release_date")
    )

    poster_path = details.get("poster_path")

    poster_url = ""

    if poster_path:
        poster_url = f"{TMDB_IMAGE_URL}{poster_path}"

    tmdb_rating = details.get("vote_average")

    # Avoid storing 0.0 when TMDb has no meaningful votes.
    if not details.get("vote_count"):
        tmdb_rating = None

    external_ids = details.get(
        "external_ids",
        {},
    )

    return {
        "tmdb_id": tmdb_id,
        "release_year": release_year,
        "rating": get_us_certification(
            details.get("release_dates", {})
        ),
        "length": details.get("runtime"),
        "genre": ", ".join(genres),
        "director": ", ".join(
            dict.fromkeys(directors)
        ),
        "cast": ", ".join(cast_names),
        "collection": collection_name,
        "studio": ", ".join(studios),
        "poster_url": poster_url,
        "overview": details.get("overview", ""),
        "tmdb_rating": tmdb_rating,
        "imdb_id": external_ids.get(
            "imdb_id",
            "",
        ),
        "tmdb_last_updated": timezone.now(),
        "tmdb_update_failed": False,
        "tmdb_error_message": "",
    }


def update_movie_from_tmdb(movie_id: int) -> bool:
    """
    Update one movie without modifying its Format or IMDb rating.

    QuerySet.update() is intentional. It bypasses save() signals,
    preventing the TMDb update from triggering itself forever.
    """

    try:
        movie = Movie.objects.get(pk=movie_id)

    except Movie.DoesNotExist:
        logger.warning(
            "Movie %s no longer exists.",
            movie_id,
        )
        return False

    try:
        metadata = build_movie_metadata(movie)

        Movie.objects.filter(
            pk=movie_id
        ).update(**metadata)

        logger.info(
            'Updated "%s" from TMDb.',
            movie.title,
        )

        return True

    except TMDbError as error:
        Movie.objects.filter(
            pk=movie_id
        ).update(
            tmdb_update_failed=True,
            tmdb_error_message=str(error)[:255],
        )

        logger.warning(
            'Could not update "%s": %s',
            movie.title,
            error,
        )

        return False

    except Exception as error:
        Movie.objects.filter(
            pk=movie_id
        ).update(
            tmdb_update_failed=True,
            tmdb_error_message=str(error)[:255],
        )

        logger.exception(
            'Unexpected error updating "%s".',
            movie.title,
        )

        return False