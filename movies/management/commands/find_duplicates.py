from django.core.management.base import BaseCommand
from django.db.models import Count

from movies.models import Movie


class Command(BaseCommand):
    help = "Find duplicate movie records by title and release year."

    def handle(self, *args, **options):
        duplicates = (
            Movie.objects
            .values(
                "title",
                "release_year",
            )
            .annotate(
                record_count=Count("id")
            )
            .filter(
                record_count__gt=1
            )
            .order_by(
                "title",
                "release_year",
            )
        )

        duplicate_groups = list(duplicates)

        if not duplicate_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    "No duplicate movie records were found."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {len(duplicate_groups)} duplicate groups:"
            )
        )

        for group in duplicate_groups:
            title = group["title"]
            release_year = group["release_year"]
            record_count = group["record_count"]

            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"{title} ({release_year}) — "
                    f"{record_count} records"
                )
            )

            matching_movies = Movie.objects.filter(
                title=title,
                release_year=release_year,
            ).order_by("pk")

            for movie in matching_movies:
                self.stdout.write(
                    f"  Database ID: {movie.pk} | "
                    f"TMDb ID: {movie.tmdb_id or 'None'} | "
                    f"Media path: "
                    f"{getattr(movie, 'media_path', '') or 'None'}"
                )