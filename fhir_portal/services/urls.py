from django.urls import include, path
from .views import audit, auth, appointments, hl7, notifications, observations, patients, roles, telemedicine, analytics

urlpatterns = [
    path('hl7-parser/', include((hl7.urlpatterns, 'hl7'), namespace='hl7-parser')),
    path('patients/', include((patients.urlpatterns, 'patients'), namespace='patients')),
    path('observations/', include((observations.urlpatterns, 'observations'), namespace='observations')),
    path('appointments/', include((appointments.urlpatterns, 'appointments'), namespace='appointments')),
    path('auth/', include((auth.urlpatterns, 'auth'), namespace='auth')),
    path('roles/', include((roles.urlpatterns, 'roles'), namespace='roles')),
    path('telemedicine/', include((telemedicine.urlpatterns, 'telemedicine'), namespace='telemedicine')),
    path('notifications/', include((notifications.urlpatterns, 'notifications'), namespace='notifications')),
    path('analytics/', include((analytics.urlpatterns, 'analytics'), namespace='analytics')),
    path('audit/', include((audit.urlpatterns, 'audit'), namespace='audit')),
]
