from django.urls import path

from apps.rating.api import AthletesRatingView, RegionsRatingView, TopRatingView

urlpatterns = [
    path("top/", TopRatingView.as_view(), name="rating-top"),
    path("athletes/", AthletesRatingView.as_view(), name="rating-athletes"),
    path("regions/", RegionsRatingView.as_view(), name="rating-regions"),
]
