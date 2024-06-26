import {
  Field,
  FieldInputProps,
  FieldProps,
  FormikProps,
  FormikValues,
  useField,
  useFormikContext,
} from "formik";
import Select from "react-select";
import makeAnimated from "react-select/animated";
import config from "@/tailwind.config";
import { getDataSetList, getProjects } from "@/api/datasets";
import { useEffect, useState } from "react";

type Option = {
  value: number;
  label: string | undefined;
};

type GroupedOption = {
  label: string;
  options: Option[];
};

async function fetchDataset(dataPartner: string): Promise<GroupedOption[]> {
  const datasets = await getDataSetList(dataPartner);
  const projects = await getProjects();

  // Initialize projectMap with all projects, ensuring each is represented
  const projectMap = new Map<number, GroupedOption>();
  projects.forEach((project) => {
    projectMap.set(project.id, {
      label: `Project: ${project.name}`,
      options: [], // Initially empty, to be filled with datasets or a placeholder
    });
  });

  // Process datasets, adding them to the appropriate project group in projectMap
  datasets.forEach((dataset) => {
    dataset.projects.forEach((projectId) => {
      const projectGroup = projectMap.get(projectId);
      if (projectGroup) {
        projectGroup.options.push({
          value: dataset.id,
          label: dataset.name,
        });
      }
    });
  });

  // Ensure all projects without datasets have a "None" option
  projectMap.forEach((group, projectId) => {
    if (group.options.length === 0) {
      group.options.push({
        value: -1, // A placeholder value for "None"
        label:
          "None in this Project. Please choose another Data Partner or Create a new Dataset",
      });
    }
  });

  return Array.from(projectMap.values());
}

const CustomSelect = ({
  field,
  form,
  isMulti = false,
  options,
  placeholder,
  isDisabled,
  required,
}: {
  options?: GroupedOption[];
  placeholder: string;
  isMulti: boolean;
  field: FieldInputProps<any>;
  form: FormikProps<any>;
  isDisabled: boolean;
  required?: boolean;
}) => {
  const animatedComponents = makeAnimated();
  const onChange = (newValue: any, actionMeta: any) => {
    const selectedValues = isMulti
      ? (newValue as Option[]).map((option) => option.value)
      : (newValue as Option).value;

    form.setFieldValue(field.name, selectedValues);
    console.log(selectedValues);
  };

  const selected = () => {
    const flattenedOptions = options
      ? options.flatMap((group) => group.options)
      : [];
    return flattenedOptions.filter((option: Option) =>
      Array.isArray(field.value)
        ? field.value.includes(option.value)
        : field.value === option.value
    );
  };

  return (
    <Select
      name={field.name}
      value={selected()}
      onChange={onChange}
      placeholder={placeholder}
      options={options}
      isMulti={isMulti}
      className="w-full"
      isDisabled={isDisabled}
      components={animatedComponents}
      styles={{
        singleValue: (base) => ({
          ...base,
          fontSize: "17px",
          color: `${config.theme.extend.colors.carrot.DEFAULT}`,
        }),
      }}
      required={required}
    />
  );
};

export const FormikSelectDataset = ({
  name,
  placeholder,
  isMulti,
  isDisabled,
  required,
}: {
  name: string;
  placeholder: string;
  isMulti: boolean;
  isDisabled: boolean;
  required?: boolean;
}) => {
  const {
    values: { dataPartner },
  } = useFormikContext<FormikValues>();

  const [datasets, setOptions] = useState<GroupedOption[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      if (dataPartner !== 0) {
        const dataset = await fetchDataset(dataPartner.toString());
        setOptions(dataset);
      }
    };
    fetchData();
  }, [dataPartner]);

  return (
    <Field name={name}>
      {({ field, form }: FieldProps<any>) => (
        <CustomSelect
          field={field}
          form={form}
          isMulti={isMulti}
          options={datasets}
          placeholder={placeholder}
          isDisabled={isDisabled}
          required={required}
        />
      )}
    </Field>
  );
};
