from django.test import TestCase
from .services import process_scan_report_sheet_table, build_usagi_index, run_usagi
import time, requests, os, json

from .models import ScanReport, DataPartner, ScanReportTable, ScanReportField, ScanReportValue, DataDictionary
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from django.core import serializers
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V
from django.forms.models import model_to_dict


class ServiceTests(TestCase):
    def test_process_scan_report_sheet_table(self):

        # Tell it what file you want to process
        filename = "/api/mapping/data/value_frequency_test_data.csv"

        # Run the test on filename
        # This function is in services.py
        result = process_scan_report_sheet_table(filename)

        self.assertIs(4, len(result))

    def test_import_data_dictionary(self):
        x = import_data_dictionary()
        print(x)

    # Run this to build Usagi's index for the first time
    # Takes a long time to run!
    def test_build_usagi_index(self):
        x = build_usagi_index()
        print(x)

    # Run this to get Usagi going
    def test_run_usagi(self):
        x = run_usagi()
        print(x)

    # Run this to get data back from Azure NLP for Health Services
    def test_nlp(self):
        
        user = User.objects.get_or_create(
            username="testuser")[0]
         
        data_partner=DataPartner.objects.create(
            name="UoN"
        )
        
        sr = ScanReport.objects.create(
            data_partner = data_partner,
            author = user,
            name = "Foobar",
            dataset = "Dataset A",
            file = SimpleUploadedFile(
                "best_file_eva.txt",
                b"these are the file contents!"   # note the b in front of the string [bytes]
            )
        )
        
        srt=ScanReportTable.objects.create(
            scan_report = sr,
            name = "Occupation"
        )
        
        srf=ScanReportField.objects.create(
            scan_report_table = srt,
            name = "Occupation",
            description_column = "Test Field",
            type_column = "VARCHAR",
            max_length = 32,
            nrows = 1,   
            nrows_checked = 1,
            fraction_empty = 50.85,
            nunique_values = 100,
            fraction_unique = 12.5,
            ignore_column = False,
            is_patient_id = False,
            is_date_event = False,
            is_ignore = False,
            classification_system = None,
            date_type = "DOB",
            concept_id = None
        )
        
        srv=ScanReportValue.objects.create(
            scan_report_field = srf,
            value = "Clinical Nurse",
            frequency = 5,
            conceptID = -1
        )
        
        obj = DataDictionary.objects.create(
            source_value=srv,
            dictionary_table="Occupation",
            dictionary_field="Occupation",
            dictionary_field_description="The occupation of the staff member",
            dictionary_value_code="Clinical Nurse",
            dictionary_value_description="This member of staff id a clinical nurse",
            definition_fixed=True
   
        )
        
        qs = DataDictionary.objects.all()

        # Create a concat field for NLP to work from
        # V is imported from models, used to comma separate other fields
        qs = qs.annotate(
            nlp_string=Concat(
                "source_value__scan_report_field__name",
                V(", "),
                "source_value__value",
                V(", "),
                "dictionary_field_description",
                V(", "),
                "dictionary_value_description",
                output_field=CharField(),
            )
        )
    
        
        # Create object to convert to JSON
        for_json = qs.values(
            "id",
            "source_value__value",
            "source_value__scan_report_field__name",
            "nlp_string",
        )

        print('QUERYSET FOR JSON >>> ', for_json)
        
        documents = []
        
        for row in for_json:
            documents.append({
                'language':'en',
                'id':row['id'],
                'text':row['nlp_string']
            })
            
        print({"documents":documents})
        
        # What the JSON to MS NLP needs to look like
        # using the above queryset as an example input string
        
        # {
        # "documents": [
        #     {
        #     "language": "en",
        #     "id": "1", 
        #     "text": "Occupation, Clinical Nurse, The occupation of the staff member, This member of staff id a clinical nurse"
        #     }
        # ]
        # }
        
        
        # POST
        url = "https://ccnett2.cognitiveservices.azure.com/text/analytics/v3.1-preview.3/entities/health/jobs?stringIndexType=TextElements_v8"
        payload = json.dumps({"documents":documents})
        headers = {
            "Ocp-Apim-Subscription-Key": os.environ.get("NLP_API_KEY"),
            "Content-Type": "application/json; utf-8",
        }

        response = requests.post(url, headers=headers, data=payload)
        print("POST STATUS CODE >>> ", response.status_code)
        print("POST REASON >>> ", response.reason)
        print(dir(response))

        # Add a short artificial wait to give the NLP service
        # time to run the job
        print('Short artifical wait...')
        time.sleep(10)

        # # GET
        get_response = requests.get(
            response.headers["operation-location"], headers=headers
        )
        print('GET STATUS CODE >>> ', get_response.status_code)
        x = get_response.json()
        print(x.items())



        # print(json.dumps(x, indent=4))