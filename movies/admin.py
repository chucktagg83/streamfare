from django.contrib import admin
from .models import Movie


# Register your models here.

@admin.register(Movie)
class MovieDatabaseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "release_year",
        "genre",
        "director",
        "imdb_rating",
        "format",
    )

    search_fields = (
        "title",
        "director",
        "cast",
    )

    list_filter = (
        "genre",
        "rating",
        "format",
    )
    
    ordering = ("title",)
    
