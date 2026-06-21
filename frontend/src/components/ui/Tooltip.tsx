import {
  cloneElement,
  isValidElement,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type FocusEvent,
  type MouseEvent,
  type MutableRefObject,
  type ReactElement,
  type ReactNode,
  type Ref,
} from "react";
import { createPortal } from "react-dom";

import "./Tooltip.css";

type TooltipPlacement = "top" | "bottom";

type TooltipProps = {
  content: ReactNode;
  children: ReactElement;
  delayMs?: number;
};

const GAP = 8;

function mergeRefs<T>(...refs: Array<Ref<T> | undefined>) {
  return (node: T | null) => {
    for (const ref of refs) {
      if (typeof ref === "function") {
        ref(node);
      } else if (ref && typeof ref === "object") {
        (ref as MutableRefObject<T | null>).current = node;
      }
    }
  };
}

function isDisabledElement(element: ReactElement): boolean {
  const props = element.props as { disabled?: boolean; "aria-disabled"?: boolean | "true" | "false" };
  return props.disabled === true || props["aria-disabled"] === true || props["aria-disabled"] === "true";
}

function hasTooltipContent(content: ReactNode): boolean {
  if (content == null || content === false) return false;
  if (typeof content === "string") return content.trim().length > 0;
  return true;
}

export function Tooltip({ content, children, delayMs = 300 }: TooltipProps) {
  const tooltipId = useId();
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number; placement: TooltipPlacement } | null>(null);

  const showTooltip = hasTooltipContent(content);
  const wrapDisabled = showTooltip && isDisabledElement(children);

  const clearDelay = useCallback(() => {
    if (timeoutRef.current != null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const hide = useCallback(() => {
    clearDelay();
    setVisible(false);
  }, [clearDelay]);

  const scheduleShow = useCallback(() => {
    if (!showTooltip) return;
    clearDelay();
    timeoutRef.current = window.setTimeout(() => {
      setVisible(true);
    }, delayMs);
  }, [showTooltip, delayMs, clearDelay]);

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    const tooltip = tooltipRef.current;
    if (!trigger || !tooltip) return;

    const rect = trigger.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;
    const placement: TooltipPlacement =
      spaceBelow >= tooltipRect.height + GAP || spaceBelow >= spaceAbove ? "bottom" : "top";

    const centerX = rect.left + rect.width / 2;
    const halfWidth = tooltipRect.width / 2;
    const left = Math.max(halfWidth + 8, Math.min(centerX, window.innerWidth - halfWidth - 8));
    const top = placement === "bottom" ? rect.bottom + GAP : rect.top - GAP;

    setCoords({ top, left, placement });
  }, []);

  useLayoutEffect(() => {
    if (!visible) {
      setCoords(null);
      return;
    }
    updatePosition();
  }, [visible, content, updatePosition]);

  useEffect(() => {
    if (!visible) return;
    const handleReposition = () => updatePosition();
    window.addEventListener("scroll", handleReposition, true);
    window.addEventListener("resize", handleReposition);
    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
    };
  }, [visible, updatePosition]);

  useEffect(() => () => clearDelay(), [clearDelay]);

  if (!isValidElement(children)) {
    return children;
  }

  if (!showTooltip) {
    const { title: _title, ...rest } = children.props as { title?: string };
    return cloneElement(children, rest);
  }

  const childProps = children.props as Record<string, unknown> & {
    title?: string;
    ref?: Ref<HTMLElement>;
    onMouseEnter?: (event: MouseEvent<HTMLElement>) => void;
    onMouseLeave?: (event: MouseEvent<HTMLElement>) => void;
    onFocus?: (event: FocusEvent<HTMLElement>) => void;
    onBlur?: (event: FocusEvent<HTMLElement>) => void;
  };

  const { title: _removedTitle, ref: childRef, ...restChildProps } = childProps;

  const eventHandlers = {
    onMouseEnter: (event: MouseEvent<HTMLElement>) => {
      scheduleShow();
      childProps.onMouseEnter?.(event);
    },
    onMouseLeave: (event: MouseEvent<HTMLElement>) => {
      hide();
      childProps.onMouseLeave?.(event);
    },
    onFocus: (event: FocusEvent<HTMLElement>) => {
      scheduleShow();
      childProps.onFocus?.(event);
    },
    onBlur: (event: FocusEvent<HTMLElement>) => {
      hide();
      childProps.onBlur?.(event);
    },
    "aria-describedby": visible ? tooltipId : undefined,
  };

  const trigger = wrapDisabled ? (
    <span
      ref={mergeRefs(triggerRef, childRef as Ref<HTMLElement> | undefined)}
      className="ui-tooltip__wrapper"
      {...eventHandlers}
    >
      {cloneElement(children, restChildProps)}
    </span>
  ) : (
    cloneElement(children, {
      ...restChildProps,
      ...eventHandlers,
      ref: mergeRefs(triggerRef, childRef as Ref<HTMLElement> | undefined),
    } as Record<string, unknown>)
  );

  return (
    <>
      {trigger}
      {visible &&
        createPortal(
          <div
            ref={tooltipRef}
            id={tooltipId}
            role="tooltip"
            className={`ui-tooltip${coords ? ` ui-tooltip--${coords.placement}` : ""}`}
            style={
              coords
                ? {
                    top: coords.top,
                    left: coords.left,
                  }
                : { top: -9999, left: -9999, visibility: "hidden" }
            }
          >
            {content}
          </div>,
          document.body,
        )}
    </>
  );
}
