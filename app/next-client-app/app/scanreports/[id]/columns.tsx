"use client";

import { ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/DataTableColumnHeader";
import Link from "next/link";

export const columns: ColumnDef<ScanReportTable>[] = [
  {
    id: "Name",
    accessorKey: "name",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Name" sortName="name" />
    ),
    cell: ({ row }) => {
      const id = row.original.id;
      const scan_report = row.original.scan_report;
      return (
        <Link href={`/scanreports/${scan_report}/tables/${id}`}>
          <button>{row.original.name}</button>
        </Link>
      );
    },
    enableHiding: true,
    enableSorting: true,
  },
  {
    id: "Person ID",
    accessorKey: "person_id",
    header: ({ column }) => (
      <DataTableColumnHeader
        column={column}
        title="Person ID"
        sortName="person_id"
      />
    ),
    enableHiding: true,
    enableSorting: true,
  },
  {
    id: "Event Date",
    accessorKey: "date_event",
    header: ({ column }) => (
      <DataTableColumnHeader
        column={column}
        title="Date Event"
        sortName="date_event"
      />
    ),
    enableHiding: true,
    enableSorting: true,
  },
];
