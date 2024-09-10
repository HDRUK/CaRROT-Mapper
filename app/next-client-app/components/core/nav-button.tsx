"use client";

import Link from "next/link";
import { useSelectedLayoutSegment } from "next/navigation";
import { Item } from "./nav-group";
import { Button } from "../ui/button";
import { cn } from "@/lib/utils";
import {
  LucideIcon,
  Waypoints,
  TableProperties,
  SearchCheck,
  Edit,
  FileScan,
  Download,
} from "lucide-react";

export const NavButton = ({
  path,
  parallelRoutesKey,
  item,
}: {
  path: string;
  parallelRoutesKey?: string;
  item: Item;
}) => {
  const segment = useSelectedLayoutSegment(parallelRoutesKey);
  const href = item.slug ? path + "/" + item.slug : path;
  const isActive =
    // Example home pages e.g. `/layouts`
    (!item.slug && segment === null) ||
    segment === item.segment ||
    // Nested pages e.g. `/layouts/electronics`
    segment === item.slug;
  const iconMap: { [key: string]: LucideIcon } = {
    SearchCheck,
    Waypoints,
    TableProperties,
    FileScan,
    Edit,
    Download,
  };

  const Icon = item.iconName ? iconMap[item.iconName] : null;

  return (
    <Link href={href}>
      <Button
        variant={"ghost"}
        className={cn("rounded-md px-3 py-1", {
          "bg-white hover:text-carrot hover:bg-white dark:bg-transparent":
            !isActive,
          "hover:bg-white hover:text-carrot/90 underline underline-offset-8 text-carrot dark:hover:bg-transparent":
            isActive,
        })}
      >
        {item.text} {Icon && <Icon className="ml-2 size-4" />}
      </Button>
    </Link>
  );
};
