from django.urls import path
from .views import fhir_gateway

urlpatterns = [
    path('metadata', fhir_gateway.get_capability_statement),
    path('Patient/<str:patient_id>', fhir_gateway.get_patient),
    path('', fhir_gateway.batch_operations),
]
