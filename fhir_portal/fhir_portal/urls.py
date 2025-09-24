from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('services.urls')),
    path('fhir/R4/', include('services.fhir_urls')),
]
