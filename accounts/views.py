from django.shortcuts import render
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import ProfileUpdateForm, UserUpdateForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from .models import LoginRecord, Profile, WatchSession


# Create your views here.
def login_view(request):
    return render(request, 'accounts/login.html')

def logout_view(request):
    return render(request, 'accounts/logout.html')

class SignupView(CreateView):
    template_name = "registration/signup.html"
    form_class = UserCreationForm
    success_url = reverse_lazy('login')  # Redirect to login page after successful signup


def format_watch_time(total_seconds):
    """
    Convert seconds into a readable value.

    Example:
        7,500 seconds

    Becomes:
        2 hours 5 minutes
    """

    total_seconds = total_seconds or 0

    hours = total_seconds // 3600

    remaining_seconds = total_seconds % 3600

    minutes = remaining_seconds // 60

    return {
        "hours": hours,
        "minutes": minutes,
    }


@login_required
def profile_view(request):
    """
    Display and update the currently logged-in user's profile.

    This view also calculates their viewing analytics.
    """

    # Find the user's profile.
    # If it does not exist, create it.
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # -----------------------------------
    # HANDLE THE PROFILE FORMS
    # -----------------------------------

    if request.method == "POST":
        # request.POST contains normal text fields.
        user_form = UserUpdateForm(
            request.POST,
            instance=request.user,
        )

        # request.FILES contains uploaded files.
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Your profile has been updated.",
            )

            # Redirect prevents the form from submitting again
            # when the browser is refreshed.
            return redirect("accounts:profile")

    else:
        # A GET request means the page is simply being opened.
        # Fill the forms with the user's existing information.
        user_form = UserUpdateForm(
            instance=request.user
        )

        profile_form = ProfileUpdateForm(
            instance=profile
        )

    # -----------------------------------
    # CALCULATE WATCH ANALYTICS
    # -----------------------------------

    watch_sessions = WatchSession.objects.filter(
        user=request.user
    )

    # Add together every seconds_watched value.
    watch_time_result = watch_sessions.aggregate(
        total_seconds=Sum("seconds_watched")
    )

    total_seconds = watch_time_result["total_seconds"] or 0

    formatted_watch_time = format_watch_time(total_seconds)

    # Count all viewing records.
    total_watch_sessions = watch_sessions.count()

    # Count the number marked completed.
    completed_titles = watch_sessions.filter(
        completed=True
    ).count()

    # Count unique movies.
    unique_movies_watched = (
        watch_sessions
        .values("movie")
        .distinct()
        .count()
    )

    # Get the five most recent viewing records.
    recent_watch_history = (
        watch_sessions
        .select_related("movie")
        .order_by("-last_watched_at")[:5]
    )

    # -----------------------------------
    # CALCULATE LOGIN ANALYTICS
    # -----------------------------------

    login_records = LoginRecord.objects.filter(
        user=request.user
    )

    total_logins = login_records.count()

    recent_logins = login_records[:5]

    last_login_record = login_records.first()

    # -----------------------------------
    # SEND DATA TO THE TEMPLATE
    # -----------------------------------

    context = {
        # Forms
        "user_form": user_form,
        "profile_form": profile_form,

        # Profile
        "profile": profile,

        # Watch analytics
        "watch_hours": formatted_watch_time["hours"],
        "watch_minutes": formatted_watch_time["minutes"],
        "total_watch_sessions": total_watch_sessions,
        "completed_titles": completed_titles,
        "unique_movies_watched": unique_movies_watched,
        "recent_watch_history": recent_watch_history,

        # Login analytics
        "total_logins": total_logins,
        "recent_logins": recent_logins,
        "last_login_record": last_login_record,
    }

    return render(
        request,
        "accounts/profile.html",
        context,
    )