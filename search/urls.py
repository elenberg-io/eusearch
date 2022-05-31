from django.urls import include, path
from search.views import EuSearchView
from . import views

urlpatterns = [
    path('', views.index, name='search-home'),
    path('search/<str:query>/', EuSearchView.as_view(), name='search-run'),
    path('results/', views.results_view, name='results-show'),
    # path('search_hay/', include('haystack.urls'))
]