from django.db import models
from django.conf import settings


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

    # Stores the complete TMDB poster URL
    poster_url = models.URLField(max_length=500, blank=True, null=True)
    
    video_file = models.FileField(
        upload_to="movies/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title
    

