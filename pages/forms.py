from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        
        fields = [
            "name",
            "email",
            "feedback_type",
            "media_title",
            "message",
            "rating"
        ]
        
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your name",
                }
            ),
            
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter your email",
                }
            ),
            
            "media_title": forms.TextInput(
                attrs={
                    "placeholder": "Movie or episode title",
                }
            ),
            
            "message": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Describe the issue or suggestion",
                }
            ),
            
            "rating": forms.RadioSelect(),
        }