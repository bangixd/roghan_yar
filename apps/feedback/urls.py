from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SurveyView, thanks_view
from .api_views import FeedbackViewSet

app_name = 'feedback'

urlpatterns = [
    path('survey/', SurveyView.as_view(), name='survey'),
    path('thanks/', thanks_view, name='thanks'),
]