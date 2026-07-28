import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from movies.models import Movie
from movies.services.tmdb_service import update_movie_from_tmdb


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Movie)
def detect_movie_lookup_changes(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    """
    Decide whether TMDb needs to be queried.

    TMDb is queried when:
    - A movie is first created.
    - Its title changes.
    - Its release year changes.
    """

    if raw:
        instance._needs_tmdb_update = False
        return

    # No primary key means this is a new Movie object.
    if not instance.pk:
        instance._needs_tmdb_update = True
        return

    try:
        existing_movie = Movie.objects.only(
            "title",
            "release_year",
        ).get(pk=instance.pk)

    except Movie.DoesNotExist:
        instance._needs_tmdb_update = True
        return

    title_changed = (
        existing_movie.title.strip().lower()
        != instance.title.strip().lower()
    )

    year_changed = (
        existing_movie.release_year
        != instance.release_year
    )

    instance._needs_tmdb_update = (
        title_changed or year_changed
    )


@receiver(post_save, sender=Movie)
def automatically_update_movie_metadata(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """
    Run the TMDb updater after the database save succeeds.
    """

    if raw:
        return

    should_update = (
        created
        or getattr(
            instance,
            "_needs_tmdb_update",
            False,
        )
    )

    if not should_update:
        return

    # Wait until the original database transaction succeeds.
    transaction.on_commit(
        lambda: update_movie_from_tmdb(
            instance.pk
        )
    )