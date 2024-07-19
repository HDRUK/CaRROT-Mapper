import { getScanReportPermissions } from "@/api/scanreports";
import { Forbidden } from "@/components/core/Forbidden";

export default async function ScanReportLayout({
  params,
  children,
  summary_modal,
  analyse_modal,
}: Readonly<{
  params: { id: string };
  children: React.ReactNode;
  summary_modal: React.ReactNode;
  analyse_modal: React.ReactNode;
}>) {
  const permissions = await getScanReportPermissions(params.id);
  const requiredPermissions: Permission[] = ["CanAdmin", "CanEdit", "CanView"];

  if (
    !requiredPermissions.some((permission) =>
      permissions.permissions.includes(permission)
    )
  ) {
    return (
      <div className="pt-10 px-16">
        <Forbidden />
      </div>
    );
  }
  return (
    <>
      <div>
        {analyse_modal}
        {summary_modal}
        {children}
      </div>
    </>
  );
}
