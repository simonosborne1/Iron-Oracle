import type { AppStep } from "../types";

const STEPS = [
  { key: "scan", label: "Scan Plate" },
  { key: "manuals", label: "Find Manuals" },
  { key: "specs", label: "Extract Specs" },
];

function getActiveStep(step: AppStep): number {
  if (step === "idle") return -1;
  if (step === "scanning" || step === "scan_done") return 0;
  if (step === "searching" || step === "manuals_done") return 1;
  return 2;
}

export default function ProgressIndicator({ step }: { step: AppStep }) {
  const active = getActiveStep(step);
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {STEPS.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <div className={`flex items-center gap-1.5 ${i <= active ? "text-orange-400" : "text-gray-600"}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2
              ${i < active ? "bg-orange-500 border-orange-500 text-white" :
                i === active ? "border-orange-400 text-orange-400" :
                "border-gray-600 text-gray-600"}`}>
              {i < active ? "✓" : i + 1}
            </div>
            <span className="text-xs hidden sm:block">{s.label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`w-8 h-0.5 ${i < active ? "bg-orange-500" : "bg-gray-700"}`} />
          )}
        </div>
      ))}
    </div>
  );
}
