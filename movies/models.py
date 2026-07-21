from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=75)
    release_year = models.IntegerField(null=True, blank=True)
    rating = models.CharField(max_length=5)
    length = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=150)
    director = models.CharField(max_length=75)
    cast = models.CharField(max_length=400)
    imdb_rating = models.FloatField()
    format = models.CharField(max_length=50)
    collection = models.CharField(max_length=50)
    studio = models.CharField(max_length=75)

    poster_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    # Path relative to the main NAS media folder.
    media_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=(
            "Example: Movies/Alien (1979)/Alien (1979).mp4"
        ),
    )

    def __str__(self):
        return self.title

