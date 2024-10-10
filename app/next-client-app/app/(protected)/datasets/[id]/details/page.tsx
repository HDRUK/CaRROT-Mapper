import {
  getDataPartners,
  getDataSet,
  getDataUsers,
  getDatasetPermissions,
} from "@/api/datasets";
import { getProjects } from "@/api/projects";
import { DatasetForm } from "@/components/datasets/DatasetForm";

interface DataSetListProps {
  params: {
    id: string;
  };
}

export default async function DatasetDetails({
  params: { id },
}: DataSetListProps) {
  const dataset = await getDataSet(id);
  const partners = await getDataPartners();
  const users = await getDataUsers();
  const projects = await getProjects();
  const permissions = await getDatasetPermissions(id);

  return (
    <DatasetForm
      dataset={dataset}
      dataPartners={partners}
      users={users}
      projects={projects}
      permissions={permissions.permissions}
    />
  );
}
