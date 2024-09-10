from api import deprecated_views
from django.urls import path

urlpatterns = [
    path(
        r"datasets/",
        deprecated_views.DatasetListView.as_view(),
        name="dataset_list",
    ),
    path(
        r"datasets_data_partners/",
        deprecated_views.DatasetAndDataPartnerListView.as_view(),
        name="dataset_data_partners_list",
    ),
    path(
        r"datasets/<int:pk>/",
        deprecated_views.DatasetRetrieveView.as_view(),
        name="dataset_retrieve",
    ),
    path(
        r"datasets/update/<int:pk>/",
        deprecated_views.DatasetUpdateView.as_view(),
        name="dataset_update",
    ),
    path(
        r"datasets/delete/<int:pk>/",
        deprecated_views.DatasetDeleteView.as_view(),
        name="dataset_delete",
    ),
    path(
        r"datasets/create/",
        deprecated_views.DatasetCreateView.as_view(),
        name="dataset_create",
    ),
    path(
        "datasets/<int:pk>/permissions/",
        deprecated_views.DatasetPermissionView.as_view(),
        name="dataset-permissions",
    ),
    path(
        r"contenttypeid",
        deprecated_views.GetContentTypeID.as_view(),
        name="contenttypeid",
    ),
    path(
        r"countprojects/<int:dataset>",
        deprecated_views.CountProjects.as_view(),
        name="countprojects",
    ),
    path(r"countstats/", deprecated_views.CountStats.as_view(), name="countstats"),
    path(
        r"countstatsscanreport/",
        deprecated_views.CountStatsScanReport.as_view(),
        name="countstatsscanreport",
    ),
    path(
        r"countstatsscanreporttable/",
        deprecated_views.CountStatsScanReportTable.as_view(),
        name="countstatsscanreporttable",
    ),
    path(
        r"countstatsscanreporttablefield/",
        deprecated_views.CountStatsScanReportTableField.as_view(),
        name="countstatsscanreporttablefield",
    ),
]
