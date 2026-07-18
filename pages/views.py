import requests

from django.http import HttpResponse
from django.shortcuts import render

from movies.models import Movie
from django.db.models import Q
from decouple import config
from django.shortcuts import render, get_object_or_404

def pages_home_view(request):
    featured_movies = Movie.objects.order_by("?")[:3]  # Get 5 random movies
    
    context = {
        "featured_movies": featured_movies,
    }
    
    return render(request, "pages/home.html", context)


def about_view(request):
    return render(request, "pages/about.html")


def contact_view(request):
    return render(request, "pages/contact.html")


def preview_view(request):
    return render(request, "pages/preview.html")


def search_view(request):
    query = request.GET.get("query", "").strip()
    results = Movie.objects.none()

    if query:
        results = Movie.objects.filter(
            Q(title__icontains=query)
            | Q(genre__icontains=query)
            | Q(director__icontains=query)
            | Q(cast__icontains=query)
        )

    context = {
        "query": query,
        "results": results,
    }

    return render(request, "pages/search.html", context)


def update_images_view(request):
    api_key = config("TMDB_API_KEY")
    image_base_url = "https://image.tmdb.org/t/p/w500"

    movies = Movie.objects.filter(
        Q(poster_url__isnull=True) | Q(poster_url="")
    )

    updated_count = 0

    for movie in movies:
        url = "https://api.themoviedb.org/3/search/movie"

        params = {
            "api_key": api_key,
            "query": movie.title,
            "include_adult": False,
            "language": "en-US",
            "page": 1,
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = data.get("results", [])

        if results:
            if len(results) < 1:
              print("Error title not  found: " + movie.title)
              continue
              
            poster_path = results[0].get("poster_path")

            if poster_path:
                movie.poster_url = image_base_url + poster_path
                movie.save(update_fields=["poster_url"])
                updated_count += 1

    return HttpResponse(
        f"Finished updating missing movie posters. "
        f"{updated_count} movies were updated."
    )
    
def user_profile_view(request):
    return render(request, "pages/profile.html")

def movieScreen_view(request, pk):
    video_object = get_object_or_404(Movie, pk=pk)
    
    context = {
        "video_object": video_object,
    }
    return render(request, "pages/movieScreen.html", context)