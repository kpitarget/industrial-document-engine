import type { PropsWithChildren, ReactNode } from "react";

type CardProps = PropsWithChildren<{
  title?: ReactNode;
  subtitle?: ReactNode;
  className?: string;
  actions?: ReactNode;
}>;

export function Card({ title, subtitle, className, actions, children }: CardProps) {
  return (
    <section className={["card", className || ""].join(" ").trim()}>
      {title || actions ? (
        <header className="card__header">
          <div>
            {title ? <h3 className="card__title">{title}</h3> : null}
            {subtitle ? <p className="card__subtitle">{subtitle}</p> : null}
          </div>
          {actions ? <div className="card__actions">{actions}</div> : null}
        </header>
      ) : null}
      <div className="card__body">{children}</div>
    </section>
  );
}
