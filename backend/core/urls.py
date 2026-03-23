from django.urls import path

from core.views import ping, DeficitView, SurplusView, RevenueView, ForecastAccuracyView

urlpatterns = [
    path("ping/", ping),
    path("dashboard/deficit/", DeficitView.as_view()),
    path("dashboard/surplus/", SurplusView.as_view()),
    path("dashboard/revenue/", RevenueView.as_view()),
    path("dashboard/forecast-accuracy/", ForecastAccuracyView.as_view()),
]
