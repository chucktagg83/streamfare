from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.pages_home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('search/', views.search_view, name='search'),
    path('test/', views.update_images_view, name='update_images'),
]
