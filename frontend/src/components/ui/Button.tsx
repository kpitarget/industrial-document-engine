import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "sm" | "md";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
    fullWidth?: boolean;
  }
>;

export function Button({
  variant = "secondary",
  size = "md",
  fullWidth = false,
  className,
  children,
  ...props
}: ButtonProps) {
  const widthClass = fullWidth ? "btn--full" : "";
  const classes = ["btn", `btn--${variant}`, `btn--${size}`, widthClass, className || ""]
    .join(" ")
    .trim();

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
