from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=75)
    release_year = models.IntegerField(null=True, blank=True)
    rating = models.CharField(max_length=20, blank=True)
    length = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=150, blank=True)
    director = models.CharField(max_length=150, blank=True)
    cast = models.CharField(max_length=500, blank=True)

    # Keep this for genuine IMDb ratings.
    imdb_rating = models.FloatField(null=True, blank=True)

    format = models.CharField(max_length=50, blank=True)
    collection = models.CharField(max_length=150, blank=True)
    studio = models.CharField(max_length=150, blank=True)
    poster_url = models.URLField(max_length=500, blank=True, null=True,)

    # New TMDb-specific fields
    tmdb_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
    )

    tmdb_rating = models.FloatField(
        null=True,
        blank=True,
    )

    imdb_id = models.CharField(
        max_length=20,
        blank=True,
    )

    overview = models.TextField(
        blank=True,
    )

    tmdb_last_updated = models.DateTimeField(
        null=True,
        blank=True,
    )

    tmdb_update_failed = models.BooleanField(
        default=False,
    )

    tmdb_error_message = models.CharField(
        max_length=255,
        blank=True,
    )

    def __str__(self):
        return self.title