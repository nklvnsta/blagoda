from django.urls import path

from core.views import (
    ping,
    DeficitView,
    SurplusView,
    RevenueView,
    SalesFiltersView,
    SalesSummaryView,
    ForecastAccuracyView,
    ForecastDemandChartView,
    ForecastSummaryView,
    ForecastByProductsView,
    SalesChartView,
    SalesRevenueChartView,
    SalesByShopsView,
    SalesByProductsView,
    CriticalStockView,
    ProblemProductsView,
)

urlpatterns = [
    path("ping/", ping),
    path("sales/filters/", SalesFiltersView.as_view()),
    path("sales/summary/", SalesSummaryView.as_view()),
    path("sales/by-shops/", SalesByShopsView.as_view()),
    path("sales/by-products/", SalesByProductsView.as_view()),
    path("dashboard/deficit/", DeficitView.as_view()),
    path("dashboard/surplus/", SurplusView.as_view()),
    path("dashboard/revenue/", RevenueView.as_view()),
    path("dashboard/forecast-accuracy/", ForecastAccuracyView.as_view()),
    path("forecast/demand-chart/", ForecastDemandChartView.as_view()),
    path("forecast/summary/", ForecastSummaryView.as_view()),
    path("forecast/by-products/", ForecastByProductsView.as_view()),
    path("dashboard/sales-chart/", SalesChartView.as_view()),
    path("sales/sales-chart/", SalesRevenueChartView.as_view()),
    path("dashboard/critical-stock/", CriticalStockView.as_view()),
    path("dashboard/problem-products/", ProblemProductsView.as_view()),
]
