from django.db import models

# Create your models here.
# Create a Class (Model) for the Movie database table
class Movie(models.Model):
    # Create the fields for the Movie database table
    title = models.CharField(max_length=75)
    release_year = models.IntegerField(null=True, blank=True)
    rating = models.CharField(max_length=5)
    length = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=150)
    director = models.CharField(max_length=75)
    cast = models.CharField(max_length=200)
    imdb_rating = models.FloatField()
    format = models.CharField(max_length=50)
    collection = models.CharField(max_length=50)
    studio = models.CharField(max_length=75)
    
def __str__(self):
    return self.title