from django.conf import settings
from django.db import models


class Profile(models.Model):
    """
    Stores additional information about a user.

    Django's normal User model already stores:
    - username
    - first name
    - last name
    - email
    - password

    This Profile model stores information that the
    normal User model does not include.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,

        # If the user is deleted, also delete the profile.
        on_delete=models.CASCADE,

        # This allows us to write:
        # request.user.profile
        related_name="profile",
    )

    profile_picture = models.ImageField(
        # Uploaded pictures will be saved inside:
        # media/profile_pictures/
        upload_to="profile_pictures/",

        # The user does not have to upload a picture.
        blank=True,
        null=True,
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
    )

    location = models.CharField(
        max_length=100,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    date_created = models.DateTimeField(
        # Automatically saves the date when the profile is created.
        auto_now_add=True,
    )

    date_updated = models.DateTimeField(
        # Automatically updates whenever the profile is saved.
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username}'s profile"


class LoginRecord(models.Model):
    """
    Creates a historical record each time a user
    successfully logs into the website.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,

        # If the user is deleted, remove their login records.
        on_delete=models.CASCADE,

        # Allows:
        # request.user.login_records.all()
        related_name="login_records",
    )

    login_time = models.DateTimeField(
        # Automatically saves the current date and time.
        auto_now_add=True,
    )

    ip_address = models.GenericIPAddressField(
        # IP address may not always be available.
        blank=True,
        null=True,
    )

    user_agent = models.TextField(
        # The user agent may tell you which browser was used.
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"

class Meta:
        # Show newest logins first.
        ordering = ["-login_time"]


class WatchSession(models.Model):
    """
    Stores a user's movie or episode viewing activity.

    Each record answers questions such as:
    - What did the user watch?
    - How many seconds did they watch?
    - Did they finish it?
    - When did they watch it?
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_sessions",
    )

    movie = models.ForeignKey(
        # Change "movies.Movie" if your Movie model has another name.
        "movies.Movie",
        on_delete=models.CASCADE,
        related_name="watch_sessions",
    )

    seconds_watched = models.PositiveIntegerField(
        # Start at zero seconds.
        default=0,
    )

    last_position_seconds = models.PositiveIntegerField(
        # Stores where the user stopped the video.
        # Example: 1,200 seconds means 20 minutes into the movie.
        default=0,
    )

    completed = models.BooleanField(
        default=False,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_watched_at = models.DateTimeField(
        # Updates whenever this record is saved.
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"

class Meta:
        ordering = ["-last_watched_at"]

# Create your models here.
