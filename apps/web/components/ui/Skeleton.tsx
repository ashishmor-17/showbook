import React from "react";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`animate-pulse rounded-md bg-zinc-800/80 ${className}`}
      {...props}
    />
  );
}

export function MovieCardSkeleton() {
  return (
    <div className="flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden p-2 gap-3">
      <Skeleton className="aspect-[2/3] w-full rounded-lg" />
      <div className="flex flex-col gap-2 p-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="flex gap-2 mt-1">
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-12" />
        </div>
      </div>
    </div>
  );
}
