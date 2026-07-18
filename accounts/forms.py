from django import forms
from django.contrib.auth import get_user_model

from .models import Profile


# This finds the User model being used by your project.
# It is safer than importing User directly.
User = get_user_model()


class UserUpdateForm(forms.ModelForm):
    """
    Updates information stored in Django's User model.
    """

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Email address",
                }
            ),
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Updates information stored in our Profile model.
    """

    class Meta:
        model = Profile

        fields = [
            "profile_picture",
            "bio",
            "location",
            "phone_number",
        ]

        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Tell us about yourself",
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "placeholder": "City, state, or country",
                }
            ),

            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "Phone number",
                }
            ),
        }