import pandas as pd
from django.core.management.base import BaseCommand
from movies.models import Movie


class Command(BaseCommand):
    help = "Imports movies from an Excel spreadsheet"

    def handle(self, *args, **kwargs):
        df = pd.read_excel("movies.xlsx", engine="openpyxl")

        for index, row in df.iterrows():
            Movie.objects.create(
                title=row["Title"],
                release_year=0 if pd.isna(row["Release Year"]) else int(row["Release Year"]),
                rating="" if pd.isna(row["Rating"]) else row["Rating"],
                length=0 if pd.isna(row["Length"]) else int(row["Length"]),
                genre="" if pd.isna(row["Genre"]) else row["Genre"],
                director="" if pd.isna(row["Director"]) else row["Director"],
                cast="" if pd.isna(row["Cast"]) else row["Cast"],
                imdb_rating=0 if pd.isna(row["IMDb Rating"]) else row["IMDb Rating"],
                format="" if pd.isna(row["Format"]) else row["Format"],
                collection="" if pd.isna(row["Collection"]) else row["Collection"],
            )

        self.stdout.write(self.style.SUCCESS("Movies imported successfully!"))