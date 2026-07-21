import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from movies.models import Movie


# Video formats the scanner will recognize.
VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".webm",
}


def normalize_title(value: str) -> str:
    """
    Convert titles into a simple form that is easier to compare.

    Examples:
        "The Matrix (1999)" -> "the matrix"
        "Spider-Man"        -> "spider man"
        "ALIEN"             -> "alien"
    """

    # Convert accented characters into a consistent form.
    value = unicodedata.normalize("NFKD", value)

    # Make the comparison lowercase.
    value = value.lower()

    # Replace symbols and punctuation with spaces.
    value = re.sub(r"[^a-z0-9]+", " ", value)

    # Remove extra spaces.
    return " ".join(value.split())


def extract_title_and_year(file_path: Path) -> tuple[str, int | None]:
    """
    Try to obtain a movie title and release year from a filename.

    Examples:
        Alien (1979).mp4
            title = Alien
            year = 1979

        The Matrix 1999.mkv
            title = The Matrix
            year = 1999

        Top Gun.mp4
            title = Top Gun
            year = None
    """

    # file_path.stem returns the filename without its extension.
    filename = file_path.stem

    # Replace common filename separators with spaces.
    filename = filename.replace("_", " ")
    filename = filename.replace(".", " ")

    # Look for a four-digit year from 1900 through 2099.
    year_match = re.search(r"\b((?:19|20)\d{2})\b", filename)

    year = None

    if year_match:
        year = int(year_match.group(1))

        # Everything before the year is normally the movie title.
        title = filename[: year_match.start()]
    else:
        title = filename

    # Remove brackets commonly used around years.
    title = title.replace("(", " ")
    title = title.replace(")", " ")
    title = title.replace("[", " ")
    title = title.replace("]", " ")

    # Remove common quality and encoding labels.
    title = re.sub(
        (
            r"\b("
            r"2160p|1080p|720p|480p|"
            r"blu[\s-]?ray|bluray|brrip|"
            r"web[\s-]?dl|webrip|dvdrip|"
            r"x264|x265|h264|h265|hevc|"
            r"aac|dts|remux"
            r")\b"
        ),
        " ",
        title,
        flags=re.IGNORECASE,
    )

    title = " ".join(title.split())

    return title, year


class Command(BaseCommand):
    help = (
        "Scans the NAS media library and connects video files "
        "to existing Movie records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show matches without changing the database.",
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace media_path values that are already populated.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        nas_root = Path(settings.NAS_MEDIA_ROOT)

        if not nas_root.exists():
            raise CommandError(
                f"The NAS folder could not be found: {nas_root}"
            )

        if not nas_root.is_dir():
            raise CommandError(
                f"The configured NAS path is not a folder: {nas_root}"
            )

        self.stdout.write(f"Scanning NAS library: {nas_root}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: The database will not be changed."
                )
            )

        # Load Movie records once instead of repeatedly querying the database.
        movies = list(Movie.objects.all())

        # Build a lookup table using normalized movie titles.
        #
        # Example:
        # "The Matrix" becomes the key "the matrix".
        movie_lookup: dict[str, list[Movie]] = {}

        for movie in movies:
            key = normalize_title(movie.title)
            movie_lookup.setdefault(key, []).append(movie)

        video_files = sorted(
            file_path
            for file_path in nas_root.rglob("*")
            if (
                file_path.is_file()
                and file_path.suffix.lower() in VIDEO_EXTENSIONS
            )
        )

        found_count = len(video_files)
        matched_count = 0
        updated_count = 0
        unchanged_count = 0
        unmatched_count = 0
        ambiguous_count = 0

        self.stdout.write(
            f"Found {found_count} supported video files."
        )

        for file_path in video_files:
            extracted_title, extracted_year = extract_title_and_year(
                file_path
            )

            normalized_file_title = normalize_title(extracted_title)

            possible_movies = movie_lookup.get(
                normalized_file_title,
                [],
            )

            # When several database records share a title,
            # use the year to identify the correct one.
            if len(possible_movies) > 1 and extracted_year:
                year_matches = [
                    movie
                    for movie in possible_movies
                    if movie.release_year == extracted_year
                ]

                if len(year_matches) == 1:
                    possible_movies = year_matches

            # No exact title match was found.
            if not possible_movies:
                unmatched_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"UNMATCHED: {file_path.name}"
                    )
                )
                continue

            # More than one database movie could match the file.
            if len(possible_movies) > 1:
                ambiguous_count += 1

                matched_names = ", ".join(
                    f"{movie.title} ({movie.release_year})"
                    for movie in possible_movies
                )

                self.stdout.write(
                    self.style.WARNING(
                        f"AMBIGUOUS: {file_path.name} -> "
                        f"{matched_names}"
                    )
                )
                continue

            movie = possible_movies[0]
            matched_count += 1

            # Store only the part beneath \\DeckplateLegacy\Media.
            relative_path = file_path.relative_to(nas_root).as_posix()

            if movie.media_path and not overwrite:
                unchanged_count += 1

                self.stdout.write(
                    f"SKIPPED: {movie.title} already has "
                    f"{movie.media_path}"
                )
                continue

            if movie.media_path == relative_path:
                unchanged_count += 1

                self.stdout.write(
                    f"UNCHANGED: {movie.title}"
                )
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"MATCHED: {file_path.name} -> {movie.title}"
                )
            )

            self.stdout.write(
                f"         Saving: {relative_path}"
            )

            if not dry_run:
                movie.media_path = relative_path
                movie.save(update_fields=["media_path"])

            updated_count += 1

        self.stdout.write("")
        self.stdout.write("Scan summary")
        self.stdout.write("------------------------------")
        self.stdout.write(f"Video files found: {found_count}")
        self.stdout.write(f"Matched:          {matched_count}")
        self.stdout.write(f"Updated:          {updated_count}")
        self.stdout.write(f"Unchanged:        {unchanged_count}")
        self.stdout.write(f"Unmatched:        {unmatched_count}")
        self.stdout.write(f"Ambiguous:        {ambiguous_count}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run complete. No records were changed."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Library scan complete."
                )
            )