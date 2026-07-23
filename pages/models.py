from django.db import models
from django.conf import settings

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ("broken_file", "File does not work"),
        ("poor_playback", "Poor viewing experience"),
        ("missing_media", "Missing movie or episode"),
        ("suggestion", "Suggestion"),
        ("other", "Other"),
    ]

    RATING_CHOICES = [
        (1, "1 Star"),
        (2, "2 Stars"),
        (3, "3 Stars"),
        (4, "4 Stars"),
        (5, "5 Stars"),
    ]
# Create your models here.


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    name = models.CharField(
        max_length=100,
    )
    
    email = models.EmailField()
    
    feedback_type = models.CharField(
        max_length=30,
        choices=FEEDBACK_TYPES,
    )
    
    media_title = models.CharField(
        max_length=200,
        blank=True,
    )
    
    message = models.TextField()
    
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
    )
    
    resolved = models.BooleanField(
        default=False,
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    
    def __str__(self):
        return F"{self.name} - {self.get_feedback_type_display()}"