import { cn } from "@/lib/utils";

export function CommandShortcut({ className, ...props }) {
  return (
    <span
      className={cn("ml-auto text-xs tracking-widest opacity-60", className)}
      {...props}
    />
  );
}
