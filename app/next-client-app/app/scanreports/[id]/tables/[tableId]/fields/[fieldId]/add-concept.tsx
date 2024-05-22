import { addConcept } from "@/api/concepts";
import { getScanReportField } from "@/api/scanreports";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/error";
import { Form, Formik } from "formik";
import { toast } from "sonner";

interface AddConceptProps {
  valueId: number;
  fieldId: string;
}

export default function AddConcept({ valueId, fieldId }: AddConceptProps) {
  const handleError = (error: any, message: string) => {
    if (error instanceof ApiError) {
      try {
        const errorObj = JSON.parse(error.message);
        toast.error(`${message} Error: ${errorObj.detail}`);
      } catch {
        toast.error(`${message} Error: ${error.message}`);
      }
    } else {
      toast.error(
        `${message} Error: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
    console.error(error);
  };

  const handleSubmit = async (conceptCode: number) => {
    try {
      const fieldObj = await getScanReportField(fieldId);
      await addConcept({
        concept: conceptCode,
        object_id: valueId,
        content_type: "scanreportvalue",
        creation_type: "M",
        table_id: fieldObj.scan_report_table,
      });
      toast.success("ConceptId linked to the value");
    } catch (error) {
      handleError(error, "Adding concept failed!");
    }
  };

  return (
    <Formik
      initialValues={{ concept: "" }}
      onSubmit={(data, actions) => {
        handleSubmit(Number(data.concept));
        actions.resetForm();
      }}
    >
      {({ values, handleChange, handleSubmit }) => (
        <Form onSubmit={handleSubmit}>
          <div className="flex gap-2">
            <div>
              <Input
                type="text"
                name="concept"
                value={values.concept}
                onChange={handleChange}
                required
                className="w-[180px]"
                pattern="\d*"
              />
            </div>
            <Button type="submit">Add</Button>
          </div>
        </Form>
      )}
    </Formik>
  );
}