from django.shortcuts import render

# Create your views here.
def pages_home_view(request):
    return render(request, 'pages/home.html')

def about_view(request):
    return render(request, 'pages/about.html')

def contact_view(request):
    return render(request, 'pages/contact.html')

def preview_view(request):
    return render(request, 'pages/preview.html')   

