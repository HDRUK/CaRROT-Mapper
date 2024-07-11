"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, FileUp, Plus } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Form, Formik } from "formik";
import { toast } from "sonner";
import { FormDataFilter } from "../form-components/FormikUtils";
import { Tooltips } from "../Tooltips";
import { FormikSelect } from "../form-components/FormikSelect";
import { FormikSelectDataset } from "../form-components/FormikSelectDataset";
import { FormikSelectEditors } from "../form-components/FormikSelectEditors";
import { createScanReport } from "@/api/scanreports";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useState } from "react";
import { CreateDatasetDialog } from "../datasets/CreateDatasetDialog";

interface FormData {
  name: string;
  visibility: string;
  editors: number[];
  dataset: number;
  scan_report_file: File;
  Data_dict: File;
}

export function CreateScanReportForm({
  dataPartners,
  projects,
}: {
  dataPartners: DataPartner[];
  projects: Project[];
}) {
  const [error, setError] = useState<string | null>(null);
  const partnerOptions = FormDataFilter<DataPartner>(dataPartners);
  const [reloadDataset, setReloadDataset] = useState(false);

  const handleSubmit = async (data: FormData) => {
    const formData = new FormData();
    formData.append("dataset", data.name);
    formData.append("visibility", data.visibility);
    formData.append("parent_dataset", data.dataset.toString());
    data.editors.forEach((editor) => {
      formData.append("editors", editor.toString());
    });
    formData.append("scan_report_file", data.scan_report_file);
    formData.append("data_dictionary_file", data.Data_dict);

    const response = await createScanReport(formData);

    if (response) {
      setError(response.errorMessage);
      toast.error("Upload New Scan Report failed. Fix the error(s) first");
    } else {
      toast.success("New Scan Report is being uploaded");
      setError(null);
    }
  };

  return (
    <>
      {error && (
        <Alert variant="destructive" className="mb-3">
          <div>
            <AlertTitle className="flex items-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              Upload New Scan Report Failed. Error:
            </AlertTitle>
            <AlertDescription>
              <ul>
                {error.split(" * ").map((err, index) => (
                  <li key={index}>* {err}</li>
                ))}
              </ul>
            </AlertDescription>
          </div>
        </Alert>
      )}
      <Formik
        initialValues={{
          dataPartner: 0,
          dataset: 0,
          editors: [],
          visibility: "PUBLIC",
          name: "",
          scan_report_file: new File([], ""),
          Data_dict: new File([], ""),
        }}
        onSubmit={(data) => {
          toast.info("Validating ...");
          handleSubmit(data);
        }}
      >
        {({ values, handleChange, handleSubmit, setFieldValue }) => (
          <Form
            className="w-full"
            onSubmit={handleSubmit}
            encType="multipart/form-data"
          >
            <div className="flex flex-col gap-3 text-lg">
              <div className="flex flex-col gap-2">
                <h3 className="flex">
                  Data Partner{" "}
                  <Tooltips
                    content="The Data Partner that owns the Dataset of the new Scan Report."
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/projects-datasets-and-scanreports/#access-controls"
                  />
                </h3>
                <FormikSelect
                  options={partnerOptions}
                  name="dataPartner"
                  placeholder="Choose a Data Partner"
                  isMulti={false}
                  isDisabled={false}
                  required={true}
                />
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="flex items-center">
                  {" "}
                  Dataset
                  <Tooltips
                    content="The Dataset to add the new Scan Report to."
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/projects-datasets-and-scanreports/#access-controls"
                  />
                  {values.dataPartner !== 0 && (
                    <CreateDatasetDialog
                      projects={projects}
                      dataPartnerID={values.dataPartner}
                      description={true}
                      setReloadDataset={setReloadDataset}
                    />
                  )}
                </h3>
                <FormikSelectDataset
                  name="dataset"
                  placeholder="Choose a Dataset"
                  isMulti={false}
                  isDisabled={values.dataPartner === 0}
                  required={true}
                  reloadDataset={reloadDataset}
                />
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="flex">
                  {" "}
                  Editors
                  <Tooltips
                    content="Dataset admins and editors also have Scan Report editor permissions."
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/projects-datasets-and-scanreports/#scan-report-roles"
                  />
                </h3>
                <FormikSelectEditors
                  name="editors"
                  placeholder="Choose Editors"
                  isMulti={true}
                  isDisabled={values.dataset === 0 || values.dataset === -1}
                />
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="flex">
                  {" "}
                  Scan Report Name
                  <Tooltips content="Name of the new Scan Report." />
                </h3>
                <Input
                  onChange={handleChange}
                  name="name"
                  className="text-lg text-carrot"
                  required
                />
              </div>
              <div className="flex items-center space-x-3">
                <h3 className="flex">
                  Visibility
                  <Tooltips
                    content="Setting the visibility of the new Scan Report."
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/projects-datasets-and-scanreports/#access-controls"
                  />
                </h3>
                <Switch
                  onCheckedChange={(checked) =>
                    handleChange({
                      target: {
                        name: "visibility",
                        value: checked ? "PUBLIC" : "RESTRICTED",
                      },
                    })
                  }
                  defaultChecked
                />
                <Label className="text-lg">
                  {values.visibility === "PUBLIC" ? "PUBLIC" : "RESTRICTED"}
                </Label>
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="flex">
                  {" "}
                  WhiteRabbit Scan Report
                  <Tooltips
                    content="Scan Report file generated from White Rabbit application."
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/uploading-scan-report/#the-scan-report-file-format"
                  />
                </h3>
                <div>
                  <Input
                    type="file"
                    name="scan_report_file"
                    accept=".xlsx"
                    required={true}
                    onChange={(e) => {
                      if (e.currentTarget.files) {
                        setFieldValue(
                          "scan_report_file",
                          e.currentTarget.files[0]
                        );
                      }
                    }}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <h3 className="flex">
                  {" "}
                  Data Dictionary
                  <Tooltips
                    content="Optional data dictionary to enable automatic OMOP mapping"
                    link="https://carrot4omop.ac.uk/Carrot-Mapper/uploading-scan-report/#the-data-dictionary-file-format"
                  />
                </h3>
                <div>
                  <Input
                    type="file"
                    name="Data_dict"
                    accept=".csv"
                    onChange={(e) => {
                      if (e.currentTarget.files) {
                        setFieldValue("Data_dict", e.currentTarget.files[0]);
                      }
                    }}
                  />
                </div>
              </div>
              <div className="mb-5 flex">
                <Button
                  type="submit"
                  className="px-4 py-2 bg-carrot text-white rounded text-lg"
                  disabled={
                    values.dataPartner === 0 ||
                    values.dataset === 0 ||
                    values.dataset === -1 ||
                    values.name === "" ||
                    values.scan_report_file.name === ""
                  }
                >
                  Upload Scan Report <FileUp className="ml-2" />
                </Button>
                <Tooltips content="You must be either an admin or an editor of the parent dataset to add a new scan report to it." />
              </div>
            </div>
          </Form>
        )}
      </Formik>
    </>
  );
}
