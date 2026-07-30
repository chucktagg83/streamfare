from django.core.management.base import BaseCommand

from movies.models import Movie
from movies.services.tmdb_service import (
    TMDbError,
    update_movie_from_tmdb,
)


class Command(BaseCommand):
    help = "Update movie metadata from TMDb."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update every movie, including movies already synced.",
        )

        parser.add_argument(
            "--retry-failed",
            action="store_true",
            help="Retry movies that previously failed.",
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Limit how many movies are processed.",
        )

    def handle(self, *args, **options):
        force_update = options["force"]
        retry_failed = options["retry_failed"]
        limit = options["limit"]

        movies = Movie.objects.all().order_by("title")

        if not force_update:
            movies = movies.filter(
                tmdb_last_updated__isnull=True,
            )

        if not retry_failed:
            movies = movies.filter(
                tmdb_update_failed=False,
            )

        if limit:
            movies = movies[:limit]

        movie_list = list(movies)
        total_movies = len(movie_list)

        if total_movies == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No movies need TMDb updates."
                )
            )
            return

        successful_count = 0
        failed_count = 0

        for position, movie in enumerate(
            movie_list,
            start=1,
        ):
            self.stdout.write(
                f'[{position}/{total_movies}] Updating "{movie.title}"...'
            )

            try:
                update_movie_from_tmdb(movie.pk)

                successful_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated "{movie.title}".'
                    )
                )

            except TMDbError as error:
                failed_count += 1

                Movie.objects.filter(
                    pk=movie.pk
                ).update(
                    tmdb_update_failed=True,
                    tmdb_error_message=str(error)[:255],
                )

                self.stdout.write(
                    self.style.WARNING(
                        f'Could not update "{movie.title}": {error}'
                    )
                )

            except Exception as error:
                failed_count += 1

                Movie.objects.filter(
                    pk=movie.pk
                ).update(
                    tmdb_update_failed=True,
                    tmdb_error_message=str(error)[:255],
                )

                self.stdout.write(
                    self.style.ERROR(
                        f'Unexpected error updating '
                        f'"{movie.title}": {error}'
                    )
                )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "TMDb synchronization complete:\n"
                f"  Successful: {successful_count}\n"
                f"  Failed: {failed_count}\n"
                f"  Total processed: {total_movies}"
            )
        )