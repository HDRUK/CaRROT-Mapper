import os
from datetime import date
from unittest import mock

import pytest
from datasets.views import DatasetIndex
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, TransactionTestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from shared.mapping.models import (
    Concept,
    DataPartner,
    Dataset,
    Project,
    ScanReport,
    ScanReportConcept,
    ScanReportField,
    ScanReportTable,
    ScanReportValue,
    VisibilityChoices,
)


class TestDatasetListView(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.user1 = User.objects.create(username="gandalf", password="iwjfijweifje")
        Token.objects.create(user=self.user1)
        self.user2 = User.objects.create(username="aragorn", password="ooieriofiejr")
        Token.objects.create(user=self.user2)

        # Set up a Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")
        # Set up datasets
        self.public_dataset1 = Dataset.objects.create(
            name="Places in Middle Earth",
            visibility="PUBLIC",
            data_partner=self.data_partner,
        )
        self.public_dataset2 = Dataset.objects.create(
            name="Places in Valinor",
            visibility="PUBLIC",
            data_partner=self.data_partner,
        )
        self.public_dataset3 = Dataset.objects.create(
            name="The Rings of Power",
            visibility="PUBLIC",
            data_partner=self.data_partner,
        )
        self.restricted_dataset = Dataset.objects.create(
            name="Fellowship Members",
            visibility="RESTRICTED",
            data_partner=self.data_partner,
        )
        self.restricted_dataset.viewers.add(self.user1)

        # Set up projects
        self.project1 = Project.objects.create(name="The Fellowship of the Ring")
        self.project1.members.add(self.user1, self.user2)
        self.project1.datasets.add(
            self.public_dataset1,
            self.public_dataset2,
            self.restricted_dataset,  # user2 can't see
        )
        self.project2 = Project.objects.create(name="The Two Towers")
        self.project2.members.add(self.user1)
        self.project2.datasets.add(self.restricted_dataset)
        self.project3 = Project.objects.create(name="The Return of the King")
        self.project3.datasets.add(self.public_dataset3)

        # Request factory for setting up requests
        self.factory = APIRequestFactory()

        # The view for the tests
        self.view = DatasetIndex.as_view()

    def test_dataset_returns(self):
        # Make the request for Datasets
        request = self.factory.get("/api/datasets/")
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate the user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response data
        response_data = self.view(request).data
        response_data = [obj.get("id") for obj in response_data]
        expected_objs = [
            self.public_dataset1.id,
            self.public_dataset2.id,
            self.restricted_dataset.id,
        ]

        # Assert user1 can only public_dataset1, public_dataset2
        # and restricted_dataset
        self.assertEqual(sorted(response_data), sorted(expected_objs))

        # Assert user1 can't see public_dataset3
        for obj in response_data:
            self.assertNotEqual(obj, self.public_dataset3.id)

        # Add user2 to the request; this is not automatic
        request.user = self.user2
        # Authenticate the user2
        force_authenticate(
            request,
            user=self.user2,
            token=self.user2.auth_token,
        )
        # Get the response
        response_data = self.view(request).data
        response_data = [obj.get("id") for obj in response_data]
        expected_objs = [self.public_dataset1.id, self.public_dataset2.id]

        # Assert user2 can only public_dataset1 and public_dataset2
        self.assertEqual(sorted(response_data), sorted(expected_objs))

        # Assert user2 can't see public_dataset3
        for obj in response_data:
            self.assertNotEqual(obj, self.public_dataset3.id)

    def test_dataset_filtering(self):
        # Make the request for the public_dataset1
        request = self.factory.get(
            "/api/datasets/", {"id__in": self.public_dataset1.id}
        )
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response
        response_data = self.view(request).data
        response_data = [obj.get("id") for obj in response_data]

        # Assert only got public_dataset1
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0], self.public_dataset1.id)

        # Make the request for the public_dataset3
        request = self.factory.get(
            "/api/datasets/", {"id__in": self.public_dataset3.id}
        )
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response
        response_data = self.view(request).data

        # Assert response is empty
        self.assertEqual(response_data, [])

    @mock.patch.dict(os.environ, {"AZ_FUNCTION_USER": "az_functions"}, clear=True)
    def test_az_function_user_perm(self):
        User = get_user_model()
        az_user = User.objects.create(username="az_functions")
        Token.objects.create(user=az_user)

        # Make the request for the Dataset
        request = self.factory.get("/api/datasets/")
        # Add the user to the request; this is not automatic
        request.user = az_user
        # Authenticate az_user
        force_authenticate(
            request,
            user=az_user,
            token=az_user.auth_token,
        )
        # Get the response
        response_data = self.view(request).data
        # Assert az_user can see all datasets
        self.assertEqual(len(response_data), Dataset.objects.all().count())


class TestDatasetUpdateView(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.admin_user = User.objects.create(
            username="gandalf", password="hjfiwejfiwef"
        )
        Token.objects.create(user=self.admin_user)
        self.non_admin_user = User.objects.create(
            username="aragorn", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_admin_user)
        self.non_project_user = User.objects.create(
            username="bilbo", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_project_user)

        # Set up Project
        self.project = Project.objects.create(name="The Fellowship of the Ring")
        self.project.members.add(self.admin_user, self.non_admin_user)

        # Set up Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")

        # Set up Dataset
        self.dataset = Dataset.objects.create(
            name="The Heights of Hobbits",
            visibility=VisibilityChoices.PUBLIC,
            data_partner=self.data_partner,
        )
        self.dataset.admins.add(self.admin_user)
        self.project.datasets.add(self.dataset)

        # Request factory for setting up requests
        self.client = APIClient()

    def test_update_returns(self):
        # Authenticate admin user
        self.client.force_authenticate(self.admin_user)
        #  Make the request
        response = self.client.patch(
            f"/api/v2/datasets/{self.dataset.id}/",
            data={"name": "The Two Towers"},
        )
        response_data = response.data
        # Ensure admin user can update Dataset
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data.get("name"), "The Two Towers")

    def test_non_admin_member_forbidden(self):
        # Authenticate non admin user
        self.client.force_authenticate(self.non_admin_user)
        #  Make the request
        response = self.client.patch(
            f"/api/v2/datasets/{self.dataset.id}/", data={"name": "The Two Towers"}
        )
        # Ensure non admin user is Forbidden
        self.assertEqual(response.status_code, 403)

    def test_non_project_member_forbidden(self):
        # Authenticate non project user
        self.client.force_authenticate(self.non_project_user)
        #  Make the request
        response = self.client.patch(
            f"/api/v2/datasets/{self.dataset.id}/", data={"name": "The Two Towers"}
        )
        # Ensure non project user is Forbidden
        self.assertEqual(response.status_code, 403)


class TestDatasetRetrieveView(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.admin_user = User.objects.create(
            username="gandalf", password="hjfiwejfiwef"
        )
        Token.objects.create(user=self.admin_user)
        self.non_admin_user = User.objects.create(
            username="aragorn", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_admin_user)
        self.non_project_user = User.objects.create(
            username="bilbo", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_project_user)

        # Set up Project
        self.project = Project.objects.create(name="The Fellowship of the Ring")
        self.project.members.add(self.admin_user, self.non_admin_user)

        # Set up Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")

        # Set up Dataset
        self.dataset = Dataset.objects.create(
            name="The Heights of Hobbits",
            visibility=VisibilityChoices.RESTRICTED,
            data_partner=self.data_partner,
        )
        self.dataset.viewers.add(self.non_admin_user)
        self.dataset.admins.add(self.admin_user)
        self.project.datasets.add(self.dataset)

        # Request factory for setting up requests
        self.client = APIClient()

    def test_non_admin_member_can_see(self):
        # Authenticate non admin user
        self.client.force_authenticate(self.non_admin_user)
        #  Make the request
        response = self.client.get(f"/api/v2/datasets/{self.dataset.id}/")
        # Ensure non admin user can see
        self.assertEqual(response.status_code, 200)

    def test_admin_member_can_see(self):
        # Authenticate admin user
        self.client.force_authenticate(self.admin_user)
        #  Make the request
        response = self.client.get(f"/api/v2/datasets/{self.dataset.id}/")
        # Ensure admin user can see
        self.assertEqual(response.status_code, 200)

    def test_non_project_member_forbidden(self):
        # Authenticate non project user
        self.client.force_authenticate(self.non_project_user)
        #  Make the request
        response = self.client.get(f"/api/v2/datasets/{self.dataset.id}/")
        # Ensure non project user is Forbidden
        self.assertEqual(response.status_code, 403)


class TestDatasetDeleteView(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.admin_user = User.objects.create(
            username="gandalf", password="hjfiwejfiwef"
        )
        Token.objects.create(user=self.admin_user)
        self.non_admin_user = User.objects.create(
            username="aragorn", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_admin_user)
        self.non_project_user = User.objects.create(
            username="bilbo", password="djfoiejwiofjoiewf"
        )
        Token.objects.create(user=self.non_project_user)

        # Set up Project
        self.project = Project.objects.create(name="The Fellowship of the Ring")
        self.project.members.add(self.admin_user, self.non_admin_user)

        # Set up Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")

        # Set up Dataset
        self.dataset = Dataset.objects.create(
            name="The Heights of Hobbits",
            visibility=VisibilityChoices.PUBLIC,
            data_partner=self.data_partner,
        )
        self.dataset.admins.add(self.admin_user)
        self.project.datasets.add(self.dataset)

        # Request factory for setting up requests
        self.client = APIClient()

    @pytest.mark.skip(
        reason="TODO: Carrot doesn't support this Delete dataset function yet. When it does, update test accordingly"
    )
    def test_update_returns(self):
        # Authenticate admin user
        self.client.force_authenticate(self.admin_user)
        #  Make the request
        response = self.client.delete(f"/api/datasets/delete/{self.dataset.id}/")
        # Ensure admin user can delete Dataset
        self.assertEqual(response.status_code, 204)

    @pytest.mark.skip(
        reason="TODO: Carrot doesn't support this Delete dataset function yet. When it does, update test accordingly"
    )
    def test_non_admin_member_forbidden(self):
        # Authenticate non admin user
        self.client.force_authenticate(self.non_admin_user)
        #  Make the request
        response = self.client.delete(f"/api/datasets/delete/{self.dataset.id}/")
        # Ensure non admin user is Forbidden
        self.assertEqual(response.status_code, 403)

    @pytest.mark.skip(
        reason="TODO: Carrot doesn't support this Delete dataset function yet. When it does, update test accordingly"
    )
    def test_non_project_member_forbidden(self):
        # Authenticate non project user
        self.client.force_authenticate(self.non_project_user)
        #  Make the request
        response = self.client.delete(f"/api/datasets/delete/{self.dataset.id}/")
        # Ensure non project user is Forbidden
        self.assertEqual(response.status_code, 403)


class TestScanReportListViewset(TransactionTestCase):
    def setUp(self):
        # Set up Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")

        # Set up datasets
        self.public_dataset = Dataset.objects.create(
            name="The Shire",
            visibility=VisibilityChoices.PUBLIC,
            data_partner=self.data_partner,
        )
        self.restricted_dataset = Dataset.objects.create(
            name="The Mines of Moria",
            visibility=VisibilityChoices.RESTRICTED,
            data_partner=self.data_partner,
        )

        # Set up scan reports
        self.scanreport1 = ScanReport.objects.create(
            dataset="The Heights of Hobbits",
            visibility=VisibilityChoices.PUBLIC,
            parent_dataset=self.public_dataset,
        )
        self.scanreport2 = ScanReport.objects.create(
            dataset="The Kinds of Orcs",
            visibility=VisibilityChoices.RESTRICTED,
            parent_dataset=self.public_dataset,
        )
        self.scanreport3 = ScanReport.objects.create(
            dataset="The Ents of Fangorn Forest",
            visibility=VisibilityChoices.RESTRICTED,
            parent_dataset=self.restricted_dataset,
        )
        self.scanreport4 = ScanReport.objects.create(
            dataset="The Elves of Lothlorien",
            visibility=VisibilityChoices.PUBLIC,
            parent_dataset=self.restricted_dataset,
        )

        # Set up projects
        self.project = Project.objects.create(name="The Fellowship of The Ring")
        self.project.datasets.add(self.public_dataset, self.restricted_dataset)

        # Set up API client
        self.client = APIClient()

    def test_admin_user_get(self):
        """Users who are admins of the parent dataset can see all public SRs
        and restricted SRs whose parent dataset they are the admin of.
        """
        User = get_user_model()

        # user who is an admin of the parent dataset
        admin_user = User.objects.create(username="gandalf", password="fiwuenfwinefiw")
        self.project.members.add(admin_user)
        self.public_dataset.admins.add(admin_user)
        self.restricted_dataset.admins.add(admin_user)

        # Get data admin_user should be able to see
        self.client.force_authenticate(admin_user)
        admin_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(admin_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in admin_response.data["results"]]
        )
        expected_objs = sorted(
            [
                self.scanreport1.id,
                self.scanreport2.id,
                self.scanreport3.id,
                self.scanreport4.id,
            ]
        )

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

        # user who is not an admin of the parent dataset
        non_admin_user = User.objects.create(
            username="saruman", password="fiwuenfwinefiw"
        )
        self.project.members.add(non_admin_user)

        # Get data non_admin_user should be able to see
        self.client.force_authenticate(non_admin_user)
        non_admin_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(non_admin_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in non_admin_response.data["results"]]
        )
        expected_objs = [self.scanreport1.id]

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

    def test_editor_get(self):
        """Users who are editors of the parent dataset can see all public SRs
        and restricted SRs whose parent dataset they are an editor of.
        """
        User = get_user_model()

        # user who is an editor of the parent dataset
        editor_user = User.objects.create(username="gandalf", password="fiwuenfwinefiw")
        self.project.members.add(editor_user)
        self.public_dataset.editors.add(editor_user)
        self.restricted_dataset.editors.add(editor_user)

        # Get data editor_user should be able to see
        self.client.force_authenticate(editor_user)
        editor_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(editor_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in editor_response.data["results"]]
        )
        expected_objs = sorted(
            [
                self.scanreport1.id,
                self.scanreport2.id,
                self.scanreport3.id,
                self.scanreport4.id,
            ]
        )

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

        # user who is not an editor of the parent dataset
        non_editor_user = User.objects.create(
            username="saruman", password="fiwuenfwinefiw"
        )
        self.project.members.add(non_editor_user)

        # Get data non_editor_user should be able to see
        self.client.force_authenticate(non_editor_user)
        non_editor_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(non_editor_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in non_editor_response.data["results"]]
        )
        expected_objs = [self.scanreport1.id]

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

    def test_viewer_get(self):
        """Users who are viewers of the parent dataset can see all public SRs
        and restricted SRs whose parent dataset they are a viewer of.
        """
        User = get_user_model()

        # user who is an viewer of the parent dataset
        viewer_user = User.objects.create(username="gandalf", password="fiwuenfwinefiw")
        self.project.members.add(viewer_user)
        self.public_dataset.viewers.add(viewer_user)
        self.restricted_dataset.viewers.add(viewer_user)

        # Get data viewer_user should be able to see
        self.client.force_authenticate(viewer_user)
        viewer_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(viewer_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in viewer_response.data["results"]]
        )
        expected_objs = sorted([self.scanreport1.id, self.scanreport4.id])

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

        # user who is not an viewer of the parent dataset
        non_viewer_user = User.objects.create(
            username="saruman", password="fiwuenfwinefiw"
        )
        self.project.members.add(non_viewer_user)

        # Get data non_viewer_user should be able to see
        self.client.force_authenticate(non_viewer_user)
        non_viewer_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(non_viewer_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in non_viewer_response.data["results"]]
        )
        expected_objs = [self.scanreport1.id]

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

    def test_author_get(self):
        """Authors can see all public SRs and restricted SRs they are the author of."""
        User = get_user_model()

        # user who is the author of a scan report
        author_user = User.objects.create(username="gandalf", password="fiwuenfwinefiw")
        self.project.members.add(author_user)
        self.scanreport3.author = author_user
        self.scanreport3.save()

        # Get data admin_user should be able to see
        self.client.force_authenticate(author_user)
        author_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(author_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in author_response.data["results"]]
        )
        expected_objs = sorted([self.scanreport1.id, self.scanreport3.id])

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

        # user who is not the author of a scan report
        non_author_user = User.objects.create(
            username="saruman", password="fiwuenfwinefiw"
        )
        self.project.members.add(non_author_user)

        # Get data non_author_user should be able to see
        self.client.force_authenticate(non_author_user)
        non_author_response = self.client.get("/api/v2/scanreports/")
        self.assertEqual(non_author_response.status_code, 200)
        observed_objs = sorted(
            [obj.get("id") for obj in non_author_response.data["results"]]
        )
        expected_objs = sorted([self.scanreport1.id])

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)

    @pytest.mark.skip(reason="We don't use AZ_FUNCTION_USER anymore")
    @mock.patch.dict(os.environ, {"AZ_FUNCTION_USER": "az_functions"}, clear=True)
    def test_az_function_user_get(self):
        """AZ_FUNCTION_USER can see all public SRs and restricted SRs."""
        User = get_user_model()

        # AZ_FUNCTION_USER
        az_user = User.objects.create(username="az_functions")
        self.project.members.add(az_user)
        self.scanreport3.author = az_user
        self.scanreport3.save()

        # Get data az_user should be able to see
        self.client.force_authenticate(az_user)
        az_response = self.client.get("/api/scanreports/")
        self.assertEqual(az_response.status_code, 200)
        observed_count = len(az_response.data)
        expected_count = ScanReport.objects.all().count()

        # Assert the observed results are the same as the expected
        self.assertEqual(observed_count, expected_count)

        # user who is not the AZ_FUNCTION_USER
        non_az_user = User.objects.create(username="saruman", password="fiwuenfwinefiw")
        self.project.members.add(non_az_user)

        # Get data non_az_user should be able to see
        self.client.force_authenticate(non_az_user)
        non_az_response = self.client.get("/api/scanreports/")
        self.assertEqual(non_az_response.status_code, 200)
        observed_objs = sorted([obj.get("id") for obj in non_az_response.data])
        expected_objs = sorted([self.scanreport1.id])

        # Assert the observed results are the same as the expected
        self.assertListEqual(observed_objs, expected_objs)


class TestScanReportActiveConceptFilterViewSet(TestCase):
    def setUp(self):
        # Set up Data Partner
        self.data_partner = DataPartner.objects.create(name="Silvan Elves")

        # Set up datasets
        self.public_dataset = Dataset.objects.create(
            name="The Shire",
            visibility=VisibilityChoices.PUBLIC,
            data_partner=self.data_partner,
        )
        self.restricted_dataset = Dataset.objects.create(
            name="The Mines of Moria",
            visibility=VisibilityChoices.RESTRICTED,
            data_partner=self.data_partner,
        )

        # Set up scan reports
        self.scanreport1 = ScanReport.objects.create(
            dataset="The Heights of Hobbits",
            visibility=VisibilityChoices.PUBLIC,
            parent_dataset=self.public_dataset,
            status="COMPLET",
        )
        self.scanreport2 = ScanReport.objects.create(
            dataset="The Kinds of Orcs",
            visibility=VisibilityChoices.RESTRICTED,
            parent_dataset=self.restricted_dataset,
            status="COMPLET",
        )

        # Set up projects
        self.project = Project.objects.create(name="The Fellowship of The Ring")
        self.project.datasets.add(self.public_dataset, self.restricted_dataset)

        # Set up tables/fields.values and SRConcepts. scanreportconcept1 is to a Field
        # in a public SR. scanreportconcept2 is to a Value in a public SR.
        # scanreportconcept3 is to a Field in a hidden SR in a hidden Dataset.
        # scanreportconcept4 is to a Value in a hidden SR in a hidden Dataset.
        # visibility of the SRs should not affect the output, but only the az_func_user
        # should be able to see anything through this view.
        self.scanreporttable1 = ScanReportTable.objects.create(
            scan_report=self.scanreport1,
            name="Table1",
        )
        self.scanreportfield1 = ScanReportField.objects.create(
            scan_report_table=self.scanreporttable1,
            name="Field1",
            description_column="",
            type_column="",
            max_length=32,
            nrows=0,
            nrows_checked=0,
            fraction_empty=0.0,
            nunique_values=0,
            fraction_unique=0.0,
        )
        self.scanreportvalue1 = ScanReportValue.objects.create(
            scan_report_field=self.scanreportfield1,
            value="Value1",
            frequency=0,
        )
        concept1 = Concept.objects.create(
            concept_id=1,
            concept_name="Test Concept",
            domain_id="Test Domain",
            vocabulary_id="Test Vocab",
            concept_class_id="1",
            concept_code="100",
            valid_start_date=date.today(),
            valid_end_date=date.today(),
        )
        self.scanreportconcept1 = ScanReportConcept.objects.create(
            concept=concept1,
            content_type=ContentType(ScanReportField),
            object_id=self.scanreportfield1.id,
            content_object=self.scanreportfield1,
        )
        self.scanreportconcept2 = ScanReportConcept.objects.create(
            concept=concept1,
            content_type=ContentType(ScanReportValue),
            object_id=self.scanreportvalue1.id,
            content_object=self.scanreportvalue1,
        )
        self.scanreporttable2 = ScanReportTable.objects.create(
            scan_report=self.scanreport2,
            name="Table2",
        )

        self.scanreportfield2 = ScanReportField.objects.create(
            scan_report_table=self.scanreporttable2,
            name="Field2",
            description_column="",
            type_column="",
            max_length=32,
            nrows=0,
            nrows_checked=0,
            fraction_empty=0.0,
            nunique_values=0,
            fraction_unique=0.0,
        )
        self.scanreportvalue2 = ScanReportValue.objects.create(
            scan_report_field=self.scanreportfield2,
            value="Value2",
            frequency=0,
        )
        self.scanreportconcept3 = ScanReportConcept.objects.create(
            concept=concept1,
            content_type=ContentType(ScanReportField),
            object_id=self.scanreportfield2.id,
            content_object=self.scanreportfield2,
        )
        self.scanreportconcept4 = ScanReportConcept.objects.create(
            concept=concept1,
            content_type=ContentType(ScanReportValue),
            object_id=self.scanreportvalue2.id,
            content_object=self.scanreportvalue2,
        )
        # Set up API client
        self.client = APIClient()

    @mock.patch.dict(os.environ, {"AZ_FUNCTION_USER": "az_functions"}, clear=True)
    @pytest.mark.skip(
        reason="Depends on hardcoded IDs, fix: https://github.com/Health-Informatics-UoN/CaRROT-Mapper/issues/637"
    )
    def test_az_function_user_get(self):
        """AZ_FUNCTION_USER can see all public SRs and restricted SRs."""
        User = get_user_model()

        # AZ_FUNCTION_USER
        az_user = User.objects.create(username="az_functions")
        self.project.members.add(az_user)
        self.scanreport1.author = az_user
        self.scanreport1.save()

        # Get field data az_user should be able to see
        self.client.force_authenticate(az_user)
        az_response = self.client.get(
            "/api/scanreportactiveconceptfilter/?content_type=15"
        )
        self.assertEqual(az_response.status_code, 200)
        az_response_ids = [item["id"] for item in az_response.data]
        self.assertTrue(self.scanreportconcept1.id in az_response_ids)
        self.assertTrue(self.scanreportconcept3.id in az_response_ids)

        # Get value data az_user should be able to see
        self.client.force_authenticate(az_user)
        az_response = self.client.get(
            "/api/scanreportactiveconceptfilter/?content_type=17"
        )
        self.assertEqual(az_response.status_code, 200)
        az_response_ids = [item["id"] for item in az_response.data]
        self.assertTrue(self.scanreportconcept2.id in az_response_ids)
        self.assertTrue(self.scanreportconcept4.id in az_response_ids)
