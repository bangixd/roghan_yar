from django.urls import path
from dashboard.views import DashboardSummaryView, MonthlyIncomeReportView

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('monthly-report/', MonthlyIncomeReportView.as_view(), name='monthly-report'),
]