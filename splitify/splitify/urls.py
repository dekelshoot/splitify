"""
URL configuration for splitify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

# myapp/urls.py
from django.urls import path
from web.views import HomeView, UploadView, ProcessingView, ResultView, download_file
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('processing/', ProcessingView.as_view(), name='process'),
    path('result/', ResultView.as_view(), name='result'),
    path('download/<str:filename>/', download_file, name='download_file'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) +static(settings.SEPARATED_URL, document_root=settings.SEPARATED_ROOT)
