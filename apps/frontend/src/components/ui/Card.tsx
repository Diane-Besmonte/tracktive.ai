import React from "react";

export default function Card({
  children,
  className = "",
  soft = false,
}: {
  children: React.ReactNode;
  className?: string;
  /** soft=true => subtle card (bg-bg); false => glassy gradient card */
  soft?: boolean;
}) {
  return (
    <div
      className={
        (soft
          ? "rounded-3xl border border-border bg-bg shadow-card "
          : "rounded-3xl border border-border bg-gradient-to-b from-surface to-bg shadow-card ") +
        "p-6 sm:p-8 " +
        className
      }
    >
      {children}
    </div>
  );
}
