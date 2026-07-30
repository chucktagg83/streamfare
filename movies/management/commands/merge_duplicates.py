from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from movies.models import Movie


class Command(BaseCommand):
    help = (
        "Merge duplicate movies that have the same title "
        "and release year."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the merge. Without this option, only preview changes.",
        )

    def movie_score(self, movie):
        """
        Give each duplicate record a score.

        The record with the most useful information becomes
        the main record that is kept.
        """

        score = 0

        important_fields = [
            "media_path",
            "tmdb_id",
            "poster_url",
            "overview",
            "imdb_id",
            "tmdb_rating",
            "director",
            "cast",
            "genre",
            "collection",
        ]

        for field_name in important_fields:
            if hasattr(movie, field_name):
                value = getattr(movie, field_name)

                if value not in (None, ""):
                    score += 1

        return score

    def copy_missing_values(self, keeper, duplicate):
        """
        Copy useful information from the duplicate record
        into the keeper when the keeper is missing it.
        """

        protected_fields = {
            "id",
            "pk",
            "title",
            "release_year",
        }

        changed_fields = []

        for field in Movie._meta.fields:
            field_name = field.name

            if field_name in protected_fields:
                continue

            keeper_value = getattr(keeper, field_name)
            duplicate_value = getattr(duplicate, field_name)

            keeper_is_empty = keeper_value in (None, "")
            duplicate_has_value = duplicate_value not in (None, "")

            if keeper_is_empty and duplicate_has_value:
                setattr(
                    keeper,
                    field_name,
                    duplicate_value,
                )

                changed_fields.append(field_name)

        return changed_fields

    def handle(self, *args, **options):
        apply_changes = options["apply"]

        duplicate_groups = (
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

        duplicate_groups = list(duplicate_groups)

        if not duplicate_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    "No duplicate movie records were found."
                )
            )
            return

        merged_groups = 0
        deleted_records = 0

        for group in duplicate_groups:
            title = group["title"]
            release_year = group["release_year"]

            movies = list(
                Movie.objects.filter(
                    title=title,
                    release_year=release_year,
                ).order_by("pk")
            )

            # Sort records so the most complete record is first.
            movies.sort(
                key=self.movie_score,
                reverse=True,
            )

            keeper = movies[0]
            duplicates = movies[1:]

            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"{title} ({release_year})"
                )
            )

            self.stdout.write(
                f"  Keep database ID: {keeper.pk}"
            )

            for duplicate in duplicates:
                self.stdout.write(
                    f"  Merge and delete database ID: "
                    f"{duplicate.pk}"
                )

            if not apply_changes:
                continue

            with transaction.atomic():
                all_changed_fields = set()

                for duplicate in duplicates:
                    changed_fields = self.copy_missing_values(
                        keeper,
                        duplicate,
                    )

                    all_changed_fields.update(
                        changed_fields
                    )

                if all_changed_fields:
                    keeper.save(
                        update_fields=list(
                            all_changed_fields
                        )
                    )

                for duplicate in duplicates:
                    duplicate.delete()
                    deleted_records += 1

            merged_groups += 1

        self.stdout.write("")

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Preview complete. No records were changed."
                )
            )

            self.stdout.write(
                'Run "python manage.py merge_duplicates '
                '--apply" to perform the merge.'
            )

            return

        self.stdout.write(
            self.style.SUCCESS(
                "Duplicate merge complete:\n"
                f"  Groups merged: {merged_groups}\n"
                f"  Duplicate records deleted: "
                f"{deleted_records}"
            )
        )