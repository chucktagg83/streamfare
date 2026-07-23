import requests
import mimetypes
import re

from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    StreamingHttpResponse,
)

from movies.models import Movie
from django.db.models import Q
from decouple import config
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib import messages

from .forms import FeedbackForm

def pages_home_view(request):
    featured_movies = Movie.objects.order_by("?")[:3]  # Get 5 random movies
    
    context = {
        "featured_movies": featured_movies,
    }
    
    return render(request, "pages/home.html", context)


def about_view(request):
    return render(request, "pages/about.html")


def contact_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)

            if request.user.is_authenticated:
                feedback.user = request.user

            feedback.save()

            messages.success(
                request,
                "Thank you. Your feedback has been submitted."
            )

            return redirect("pages:contact")

    else:
        initial_data = {}

        if request.user.is_authenticated:
            initial_data = {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
            }

        form = FeedbackForm(initial=initial_data)

    context = {
        "form": form,
    }

    return render(
        request,
        "pages/contact.html",
        context,
    )


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
"""
@login_required
def stream_movie_view(request, pk):
    movie = get_object_or_404(Movie, pk=pk)

    if not movie.media_path:
        raise Http404("This movie does not have a media file assigned.")

    nas_root = Path(settings.NAS_MEDIA_ROOT).resolve()
    movie_path = (nas_root / movie.media_path).resolve()

    # Security check:
    # Prevent a database path from escaping the approved NAS folder.
    try:
        movie_path.relative_to(nas_root)
    except ValueError as error:
        raise Http404("Invalid movie path.") from error

    if not movie_path.is_file():
        raise Http404("The movie file could not be found on the NAS.")

    content_type, _ = mimetypes.guess_type(movie_path.name)

    return FileResponse(
        open(movie_path, "rb"),
        content_type=content_type or "application/octet-stream",
        filename=movie_path.name,
        as_attachment=False,
    )
"""
  

def ranged_file_iterator(
    file_path: Path,
    start: int,
    length: int,
    chunk_size: int = 1024 * 1024,
):
    """
    Read only the requested section of a video file.

    chunk_size is 1 MB, so Django sends the movie gradually
    instead of loading the entire file into memory.
    """

    file_handle = open(file_path, "rb")

    try:
        file_handle.seek(start)
        remaining = length

        while remaining > 0:
            data = file_handle.read(min(chunk_size, remaining))

            if not data:
                break

            remaining -= len(data)
            yield data

    finally:
        file_handle.close()
        
@login_required        
def stream_movie_view(request, pk):
    movie = get_object_or_404(Movie, pk=pk)

    if not movie.media_path:
        raise Http404(
            "This movie does not have a media file assigned."
        )

    nas_root = Path(settings.NAS_MEDIA_ROOT).resolve()
    movie_path = (nas_root / movie.media_path).resolve()

    # Prevent a manipulated database path from leaving
    # the approved NAS Media directory.
    try:
        movie_path.relative_to(nas_root)
    except ValueError as error:
        raise Http404("Invalid movie path.") from error

    if not movie_path.is_file():
        raise Http404(
            "The movie file could not be found on the NAS."
        )

    file_size = movie_path.stat().st_size

    content_type, _ = mimetypes.guess_type(movie_path.name)
    content_type = content_type or "application/octet-stream"

    range_header = request.headers.get("Range")

    # The browser may make a HEAD request to inspect the video.
    if request.method == "HEAD":
        response = HttpResponse(
            status=200,
            content_type=content_type,
        )
        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"
        return response

    # No range requested: return the complete file as a stream.
    if not range_header:
        response = FileResponse(
            open(movie_path, "rb"),
            content_type=content_type,
            as_attachment=False,
        )

        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"
        response["Content-Disposition"] = (
            f'inline; filename="{movie_path.name}"'
        )

        return response

    # Examples:
    # Range: bytes=0-
    # Range: bytes=1000000-2000000
    match = re.match(
        r"bytes=(\d*)-(\d*)",
        range_header,
    )

    if not match:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    start_text = match.group(1)
    end_text = match.group(2)

    # Standard video requests normally provide the start value.
    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1

    # Handle suffix requests such as bytes=-500000.
    elif end_text:
        suffix_length = int(end_text)
        start = max(file_size - suffix_length, 0)
        end = file_size - 1

    else:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    end = min(end, file_size - 1)

    if start >= file_size or start > end:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    content_length = end - start + 1

    response = StreamingHttpResponse(
        ranged_file_iterator(
            movie_path,
            start,
            content_length,
        ),
        status=206,
        content_type=content_type,
    )

    response["Content-Length"] = str(content_length)
    response["Content-Range"] = (
        f"bytes {start}-{end}/{file_size}"
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Disposition"] = (
        f'inline; filename="{movie_path.name}"'
    )

    return response