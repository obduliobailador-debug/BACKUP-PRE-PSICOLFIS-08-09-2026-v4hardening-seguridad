import React from "react";
import { NavLink, useMatch, useLocation } from "react-router-dom";
import { Menu, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { navigation, primaryCta } from "./navigationConfig";

/**
 * MobileNavigation — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 5)
 *
 * Mobile/tablet navigation (< xl). Reuses the SAME navigationConfig as the
 * desktop MainNavigation (single source of truth) and the SAME active-state
 * logic (NavLink + useMatch).
 *
 * Panel = shadcn Sheet (Radix Dialog): focus trap, portal, overlay, Escape,
 * click-outside close, body scroll lock and focus return to the trigger are
 * all handled by Radix. Groups = shadcn Collapsible (real <button>, tap to
 * toggle, aria-expanded/aria-controls handled by Radix — no hover dependency).
 *
 * Only ONE submenu level exists in this architecture (no mega-menu).
 */

// Shared row styling with comfortable touch targets (>= 44px height).
const rowBase =
  "flex min-h-11 items-center rounded-md px-3 py-3 text-base transition-colors " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

function MobileLink({ item, className }) {
  return (
    <SheetClose asChild>
      <NavLink
        to={item.href}
        end={item.end}
        className={({ isActive }) =>
          cn(
            rowBase,
            "text-foreground/80 hover:bg-accent hover:text-foreground",
            isActive &&
              "font-semibold text-primary underline underline-offset-4 decoration-2",
            className,
          )
        }
      >
        {item.label}
      </NavLink>
    </SheetClose>
  );
}

function MobileGroup({ group }) {
  // Active when the current route is the group base or any descendant.
  const match = useMatch({ path: `${group.basePath}/*`, end: false });
  const isActive = Boolean(match);
  // Auto-expand the group that owns the current route.
  const [open, setOpen] = React.useState(isActive);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="border-b border-border/60">
      <CollapsibleTrigger
        className={cn(
          rowBase,
          "w-full justify-between hover:bg-accent",
          group.secondary
            ? "text-muted-foreground hover:text-foreground"
            : "text-foreground/80 hover:text-foreground",
          isActive && "font-semibold text-primary",
        )}
      >
        <span className={cn(isActive && "underline underline-offset-4 decoration-2")}>
          {group.label}
        </span>
        <ChevronDown
          className={cn(
            "h-5 w-5 shrink-0 opacity-60 transition-transform duration-200",
            open && "rotate-180",
          )}
          aria-hidden="true"
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ul className="flex flex-col pb-2 pl-3">
          {group.items.map((sub) => (
            <li key={sub.href}>
              <MobileLink item={sub} className="text-sm" />
            </li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function MobileNavigation({ className }) {
  const [open, setOpen] = React.useState(false);
  const location = useLocation();
  const isfirst = React.useRef(true);

  // Safety net: ensure the panel closes on any route change (React Router).
  React.useEffect(() => {
    if (isfirst.current) {
      isfirst.current = false;
      return;
    }
    setOpen(false);
  }, [location.pathname]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          type="button"
          aria-label="Abrir menú de navegación"
          className={cn(
            "inline-flex h-10 w-10 items-center justify-center rounded-md text-foreground " +
              "hover:bg-accent focus-visible:outline-none focus-visible:ring-2 " +
              "focus-visible:ring-ring focus-visible:ring-offset-2",
            className,
          )}
        >
          <Menu className="h-6 w-6" aria-hidden="true" />
        </button>
      </SheetTrigger>

      <SheetContent
        side="right"
        className="flex w-[88%] max-w-sm flex-col gap-0 p-0"
      >
        <SheetTitle className="border-b border-border px-4 py-4 text-base">
          Navegación
        </SheetTitle>
        <SheetDescription className="sr-only">
          Menú principal de navegación de PSICOLFISNET.
        </SheetDescription>

        {/* Scrollable navigation area (internal scroll when content overflows) */}
        <div className="flex-1 overflow-y-auto overscroll-contain px-4 py-3">
          <nav aria-label="Navegación principal">
            <ul className="flex flex-col">
              {navigation.map((item) => (
                <li key={item.label}>
                  {item.type === "group" ? (
                    <MobileGroup group={item} />
                  ) : (
                    <MobileLink item={item} />
                  )}
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* CTA matriz — pinned, respects device safe area */}
        <div
          className="border-t border-border p-4"
          style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
        >
          <SheetClose asChild>
            <Button asChild className="w-full">
              <NavLink to={primaryCta.href}>{primaryCta.label}</NavLink>
            </Button>
          </SheetClose>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default MobileNavigation;
