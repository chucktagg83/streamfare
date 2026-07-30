import pandas as pd

from django.core.management.base import BaseCommand
from movies.models import Movie


class Command(BaseCommand):
    help = "Import new movies and update spreadsheet-owned fields."

    def clean_text(self, value):
        """
        Return clean text from an Excel cell.

        Empty Excel cells become an empty string.
        """

        if pd.isna(value):
            return ""

        return str(value).strip()

    def clean_integer(self, value):
        """
        Convert an Excel value into an integer.

        Empty or invalid cells become None.
        """

        if pd.isna(value):
            return None

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return None

    def clean_float(self, value):
        """
        Convert an Excel value into a decimal number.

        Empty or invalid cells become None.
        """

        if pd.isna(value):
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None

    def handle(self, *args, **options):
        spreadsheet_path = "movies.xlsx"

        try:
            dataframe = pd.read_excel(
                spreadsheet_path,
                engine="openpyxl",
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f'Could not find "{spreadsheet_path}". '
                    "Place it beside manage.py."
                )
            )
            return

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_count = 0

        for _, row in dataframe.iterrows():
            title = self.clean_text(row.get("Title"))
            release_year = self.clean_integer(
                row.get("Release Year")
            )

            if not title:
                skipped_count += 1
                continue

            # Search for an existing movie using its title and year.
            #
            # first() prevents the command from crashing if old
            # duplicate records already exist in the database.
            movie = Movie.objects.filter(
                title__iexact=title,
                release_year=release_year,
            ).order_by("pk").first()

            created = False

            if movie is None:
                movie = Movie(
                    title=title,
                    release_year=release_year,
                )
                created = True

            spreadsheet_values = {
                "title": title,
                "release_year": release_year,
                "rating": self.clean_text(
                    row.get("Rating")
                ),
                "length": self.clean_integer(
                    row.get("Length")
                ),
                "genre": self.clean_text(
                    row.get("Genre")
                ),
                "director": self.clean_text(
                    row.get("Director")
                ),
                "cast": self.clean_text(
                    row.get("Cast")
                ),
                "imdb_rating": self.clean_float(
                    row.get("IMDb Rating")
                ),
                "format": self.clean_text(
                    row.get("Format")
                ),
                "collection": self.clean_text(
                    row.get("Collection")
                ),
            }

            changed_fields = []

            for field_name, new_value in spreadsheet_values.items():
                old_value = getattr(movie, field_name)

                if old_value != new_value:
                    setattr(movie, field_name, new_value)
                    changed_fields.append(field_name)

            if created:
                movie.save()
                created_count += 1

            elif changed_fields:
                movie.save(update_fields=changed_fields)
                updated_count += 1

            else:
                unchanged_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Spreadsheet import complete:\n"
                f"  Created: {created_count}\n"
                f"  Updated: {updated_count}\n"
                f"  Unchanged: {unchanged_count}\n"
                f"  Skipped: {skipped_count}"
            )
        )