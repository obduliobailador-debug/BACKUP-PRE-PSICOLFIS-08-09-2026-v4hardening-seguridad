import React from "react";
import { NavLink, useMatch } from "react-router-dom";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { navigation } from "./navigationConfig";

/**
 * MainNavigation — PSICOLFISNET 2.0 desktop/tablet navigation (FASE 1 · BLOQUE 4)
 *
 * Reads the centralized navigationConfig. Groups use the accessible Radix
 * DropdownMenu primitive (opens on click/keyboard, NOT hover-only; Escape
 * closes; arrow-key navigation; aria-expanded handled by Radix; closes on
 * select). Active states come from React Router (NavLink + useMatch), and are
 * signalled by weight + underline (not colour alone).
 *
 * This component is desktop-facing; MobileNavigation (BLOQUE 5) will reuse the
 * SAME navigationConfig.
 */

// Shared classes for top-level trigger/link.
const topBase =
  "inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

function TopLink({ item }) {
  return (
    <NavLink
      to={item.href}
      end={item.end}
      className={({ isActive }) =>
        cn(
          topBase,
          "text-foreground/75 hover:text-foreground",
          isActive &&
            "font-semibold text-primary underline underline-offset-8 decoration-2",
        )
      }
    >
      {item.label}
    </NavLink>
  );
}

function NavGroup({ group }) {
  // Active when the current route is the group base or any descendant.
  const match = useMatch({ path: `${group.basePath}/*`, end: false });
  const isActive = Boolean(match);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            topBase,
            group.secondary
              ? "text-muted-foreground hover:text-foreground"
              : "text-foreground/75 hover:text-foreground",
            isActive &&
              "font-semibold text-primary underline underline-offset-8 decoration-2",
          )}
        >
          {group.label}
          <ChevronDown className="h-4 w-4 opacity-60" aria-hidden="true" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-56">
        {group.items.map((sub) => (
          <DropdownMenuItem key={sub.href} asChild>
            <NavLink
              to={sub.href}
              className={({ isActive: subActive }) =>
                cn(
                  "w-full cursor-pointer",
                  subActive && "font-medium text-primary",
                )
              }
            >
              {sub.label}
            </NavLink>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function MainNavigation({ className }) {
  return (
    <nav aria-label="Navegación principal" className={cn("items-center gap-1", className)}>
      {navigation.map((item) =>
        item.type === "group" ? (
          <NavGroup key={item.label} group={item} />
        ) : (
          <TopLink key={item.label} item={item} />
        ),
      )}
    </nav>
  );
}

export default MainNavigation;
