import type { MachineIdentity } from "../types";

interface Props {
  machine: MachineIdentity;
  onFindManuals: () => void;
  loading: boolean;
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "text-green-400" : pct >= 60 ? "text-yellow-400" : "text-red-400";
  return <span className={`text-xs font-mono ${color}`}>{pct}% confidence</span>;
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-gray-100 font-medium">{value}</p>
    </div>
  );
}

export default function MachineCard({ machine, onFindManuals, loading }: Props) {
  const lowConfidence = machine.confidence < 0.7;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-orange-400">
            {machine.make ?? "Unknown Make"}
          </h2>
          <p className="text-gray-300">{machine.model ?? "Unknown Model"}</p>
        </div>
        <ConfidenceBadge value={machine.confidence} />
      </div>

      {lowConfidence && (
        <div className="bg-yellow-900/40 border border-yellow-700 rounded-lg p-3 text-yellow-300 text-sm">
          Low confidence — consider retaking the photo with better lighting.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Field label="Serial Number" value={machine.serial_number} />
        <Field label="Year" value={machine.year} />
        <Field label="Capacity" value={machine.capacity} />
        <Field label="Voltage" value={machine.voltage} />
        {machine.other_ids && Object.entries(machine.other_ids).map(([k, v]) => (
          <Field key={k} label={k} value={v} />
        ))}
      </div>

      {machine.notes && (
        <p className="text-gray-500 text-xs italic">{machine.notes}</p>
      )}

      <button
        onClick={onFindManuals}
        disabled={loading}
        className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
      >
        {loading ? "Searching…" : "Find Manuals"}
      </button>
    </div>
  );
}
