from django.db.models.query_utils import Q
from rest_framework import filters
from shared.data.models import VisibilityChoices
import os


class ScanReportAccessFilter(filters.BaseFilterBackend):
    """
    Filter that only allows users to see Scan Reports they are allowed to view, edit, or admin.
    """

    # Each model type needs a different relationship to get the Scan Report / Dataset permissions.
    RELATIONSHIP_MAPPING = {
        "scanreport": "",
        "scanreporttable": "scan_report__",
        "scanreportfield": "scan_report_table__scan_report__",
        "scanreportvalue": "scan_report_field__scan_report_table__scan_report__",
    }

    def filter_queryset(self, request, queryset, view):
        model = queryset.model.__name__.lower()
        relationship = self.RELATIONSHIP_MAPPING.get(model, "")
        print(model, relationship)
        user_id = request.user.id

        visibility_conditions = self.get_visibility_conditions(relationship)
        permission_conditions = self.get_permission_conditions(relationship, user_id)
        print(visibility_conditions, permission_conditions)
        print(
            queryset.filter((visibility_conditions & permission_conditions)).distinct()
        )
        return queryset.filter(
            (visibility_conditions & permission_conditions)
        ).distinct()

    def get_visibility_conditions(self, relationship: str) -> Q:
        """
        Get visibility conditions for a given relationship.

        Args:
            relationship (str): The relationship for which visibility conditions are needed.

        Returns:
            Q: Query object representing the visibility conditions.
        """
        dataset_visibility = f"{relationship}parent_dataset__visibility"
        scan_report_visibility = f"{relationship}visibility"

        return Q(
            Q(**{dataset_visibility: VisibilityChoices.PUBLIC})
            | Q(**{dataset_visibility: VisibilityChoices.RESTRICTED})
        ) & Q(
            Q(**{scan_report_visibility: VisibilityChoices.PUBLIC})
            | Q(**{scan_report_visibility: VisibilityChoices.RESTRICTED})
        )

    def get_permission_conditions(self, relationship: str, user_id: str) -> Q:
        """
        Get permission conditions for a given relationship and user.

        Args:
            relationship (str): The relationship for which permission conditions are needed.
            user_id (str): The user ID for which permission conditions are generated.

        Returns:
            Q: Query object representing the permission conditions.
        """
        scan_report_viewers = f"{relationship}viewers"
        scan_report_editors = f"{relationship}editors"
        scan_report_author = f"{relationship}author"
        dataset_viewers = f"{relationship}parent_dataset__viewers"
        dataset_editors = f"{relationship}parent_dataset__editors"
        dataset_admins = f"{relationship}parent_dataset__admins"
        project_members = f"{relationship}parent_dataset__project__members"

        return Q(
            Q(**{scan_report_viewers: user_id})
            | Q(**{scan_report_editors: user_id})
            | Q(**{scan_report_author: user_id})
            | Q(**{dataset_viewers: user_id})
            | Q(**{dataset_editors: user_id})
            | Q(**{dataset_admins: user_id})
            | Q(**{project_members: user_id})
        )


class ScanReportAccessFilterV2(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user

        if user.username == os.getenv("AZ_FUNCTION_USER"):
            return queryset

        return (
            queryset.filter(
                (
                    Q(parent_dataset__visibility=VisibilityChoices.PUBLIC)
                    & (
                        Q(visibility=VisibilityChoices.PUBLIC)
                        | (
                            Q(visibility=VisibilityChoices.RESTRICTED)
                            & (
                                Q(viewers=user.id)
                                | Q(editors=user.id)
                                | Q(author=user.id)
                                | Q(parent_dataset__editors=user.id)
                                | Q(parent_dataset__admins=user.id)
                            )
                        )
                    )
                )
                | (
                    Q(parent_dataset__visibility=VisibilityChoices.RESTRICTED)
                    & (
                        Q(parent_dataset__admins=user.id)
                        | Q(parent_dataset__editors=user.id)
                        | (
                            Q(parent_dataset__viewers=user.id)
                            & (
                                Q(viewers=user.id)
                                | Q(editors=user.id)
                                | Q(author=user.id)
                                | Q(visibility=VisibilityChoices.PUBLIC)
                            )
                        )
                    )
                )
            )
            .filter(parent_dataset__project__members=user.id)
            .distinct()
        )
