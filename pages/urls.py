from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.pages_home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("search/", views.search_view, name="search"),
    path("test/", views.update_images_view, name="update_images"),
    path("profile/", views.user_profile_view, name="user_profile"),

    path(
        "movie/<int:pk>/",
        views.movieScreen_view,
        name="movie-screen",
    ),

    path(
        "movie/<int:pk>/stream/",
        views.stream_movie_view,
        name="stream-movie",
    ),
]