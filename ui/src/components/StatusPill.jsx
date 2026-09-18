import { CheckCircle2, CircleAlert, LoaderCircle } from "lucide-react";

export default function StatusPill({ status, message }) {
  const styles = {
    connected: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
    disconnected: "border-rose-400/25 bg-rose-400/10 text-rose-300",
    checking: "border-amber-300/25 bg-amber-300/10 text-amber-200",
  };
  const Icon = status === "connected" ? CheckCircle2 : status === "disconnected" ? CircleAlert : LoaderCircle;

  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${styles[status]}`}>
      <Icon size={14} className={status === "checking" ? "animate-spin" : ""} />
      {message}
    </span>
  );
}
