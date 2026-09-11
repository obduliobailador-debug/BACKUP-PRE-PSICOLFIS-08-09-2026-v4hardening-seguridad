import { useEffect, useRef } from "react";

/**
 * useModalA11y — dependency-free modal accessibility for legacy modals.
 *
 * Handles: initial focus, focus trap (Tab/Shift+Tab), Escape to close,
 * focus return to the trigger on close, and background scroll lock.
 * Does not alter markup, text, styles or business logic — the caller just
 * spreads role/aria attributes and attaches the returned ref to the dialog.
 *
 * @param {{ isOpen: boolean, onClose: () => void }} opts
 * @returns {import('react').RefObject<HTMLElement>} ref for the dialog element
 */
const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

export function useModalA11y({ isOpen, onClose }) {
  const ref = useRef(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const node = ref.current;
    if (!node) return undefined;

    const previouslyFocused = document.activeElement;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const getFocusable = () =>
      Array.from(node.querySelectorAll(FOCUSABLE)).filter(
        (el) => el.offsetParent !== null,
      );

    // Initial focus: first focusable element, fallback to the dialog itself.
    const initial = getFocusable();
    (initial[0] || node).focus();

    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onCloseRef.current();
        return;
      }
      if (e.key !== "Tab") return;
      const items = getFocusable();
      if (items.length === 0) {
        e.preventDefault();
        node.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      if (e.shiftKey) {
        if (active === first || !node.contains(active)) {
          e.preventDefault();
          last.focus();
        }
      } else if (active === last || !node.contains(active)) {
        e.preventDefault();
        first.focus();
      }
    };

    node.addEventListener("keydown", onKeyDown);
    return () => {
      node.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prevOverflow;
      if (previouslyFocused && typeof previouslyFocused.focus === "function") {
        previouslyFocused.focus();
      }
    };
  }, [isOpen]);

  return ref;
}
