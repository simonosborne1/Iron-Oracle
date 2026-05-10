import { useState, useEffect } from "react";
import type { MachineIdentity } from "../types";

interface Props {
  machine: MachineIdentity;
  onFindManuals: (make: string, model: string, serial: string) => void;
  loading: boolean;
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "text-green-400" : pct >= 60 ? "text-yellow-400" : "text-red-400";
  return <span className={`text-xs font-mono ${color}`}>{pct}% confidence</span>;
}

const inputClass =
  "bg-gray-800 text-white rounded-lg px-3 py-2.5 w-full focus:outline-none focus:ring-2 focus:ring-orange-500 text-base";

export default function MachineCard({ machine, onFindManuals, loading }: Props) {
  const [make, setMake] = useState(machine.make ?? "");
  const [model, setModel] = useState(machine.model ?? "");
  const [serial, setSerial] = useState(machine.serial_number ?? "");

  // Re-sync fields if a new scan result arrives
  useEffect(() => {
    setMake(machine.make ?? "");
    setModel(machine.model ?? "");
    setSerial(machine.serial_number ?? "");
  }, [machine]);

  const isManual = machine.notes === "Manually entered";
  const lowConfidence = !isManual && machine.confidence < 0.7;
  const canSearch = make.trim() || model.trim() || serial.trim();

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
          {isManual ? "Manual Entry" : "Plate Identified"}
        </p>
        {!isManual && <ConfidenceBadge value={machine.confidence} />}
      </div>

      {lowConfidence && (
        <div className="bg-yellow-900/40 border border-yellow-700 rounded-lg p-3 text-yellow-300 text-sm">
          Low confidence — check and correct the fields below if needed.
        </div>
      )}

      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 uppercase tracking-wide">Make</label>
          <input
            value={make}
            onChange={(e) => setMake(e.target.value)}
            placeholder="e.g. Skyjack"
            className={inputClass}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 uppercase tracking-wide">Model</label>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="e.g. SJ1256THS"
            className={inputClass}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 uppercase tracking-wide">Serial Number</label>
          <input
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            placeholder="e.g. 87410194"
            className={inputClass}
          />
        </div>

        {/* Read-only supplementary fields */}
        {(machine.year || machine.capacity) && (
          <div className="grid grid-cols-2 gap-2 pt-1">
            {machine.year && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Year</p>
                <p className="text-gray-300 text-sm font-medium">{machine.year}</p>
              </div>
            )}
            {machine.capacity && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Capacity</p>
                <p className="text-gray-300 text-sm font-medium">{machine.capacity}</p>
              </div>
            )}
          </div>
        )}
      </div>

      <button
        onClick={() => onFindManuals(make.trim(), model.trim(), serial.trim())}
        disabled={loading || !canSearch}
        className="w-full py-3 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
      >
        {loading ? "Searching…" : "Find Manuals"}
      </button>
    </div>
  );
}
