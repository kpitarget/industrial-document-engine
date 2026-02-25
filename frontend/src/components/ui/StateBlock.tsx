import type { ReactNode } from "react";

type StateBlockProps = {
  title: string;
  message: string;
  tone?: "neutral" | "error" | "loading";
  action?: ReactNode;
};

export function StateBlock({ title, message, tone = "neutral", action }: StateBlockProps) {
  return (
    <div className={`state-block state-block--${tone}`}>
      <h4>{title}</h4>
      <p>{message}</p>
      {action ? <div className="state-block__action">{action}</div> : null}
    </div>
  );
}
