from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('surveys/', include('surveys.urls', namespace='surveys')),  # Utilisation du namespace
    path('', RedirectView.as_view(pattern_name='surveys:list', permanent=False)),  # Redirection vers la liste des sondages
]

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir également les fichiers statiques en développement
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)