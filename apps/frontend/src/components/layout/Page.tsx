import React from "react";

export default function Page({
  children,
  maxWidth = "max-w-6xl",
  withBlobs = true,
  className = "",
}: {
  children: React.ReactNode;
  maxWidth?: string;
  withBlobs?: boolean;   // set false if a page shouldn’t have background blobs
  className?: string;
}) {
  return (
    <>
      {withBlobs && (
        <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute -top-24 -left-20 h-72 w-72 rounded-full blur-3xl opacity-30 bg-gradient-to-tr from-primary to-[#77b7c5]" />
          <div className="absolute -bottom-24 -right-20 h-72 w-72 rounded-full blur-3xl opacity-25 bg-gradient-to-tr from-[#a3c2e0] to-primary" />
        </div>
      )}
      <main className={`px-4 ${className}`}>
        <section className={`mx-auto ${maxWidth} py-8 sm:py-12`}>
          {children}
        </section>
      </main>
    </>
  );
}
