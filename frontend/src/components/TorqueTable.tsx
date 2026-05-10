import type { TorqueSpec } from "../types";

interface Props { specs: TorqueSpec[]; }

function formatValue(val: number | null, max: number | null): string {
  if (val === null) return "—";
  if (max !== null) return `${val}–${max}`;
  return String(val);
}

function downloadCSV(specs: TorqueSpec[]) {
  const header = "Component,Fastener,ft-lb (min),ft-lb (max),Nm (min),Nm (max),Notes,Page";
  const rows = specs.map((s) =>
    [s.component, s.fastener, s.torque_ftlb ?? "", s.torque_ftlb_max ?? "",
     s.torque_nm ?? "", s.torque_nm_max ?? "", s.notes ?? "", s.page_ref ?? ""]
      .map((v) => `"${String(v).replace(/"/g, '""')}"`)
      .join(",")
  );
  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "torque_specs.csv";
  a.click();
}

export default function TorqueTable({ specs }: Props) {
  if (specs.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-400">No torque specifications found in this manual.</p>
      </div>
    );
  }

  // Group by component
  const groups = specs.reduce<Record<string, TorqueSpec[]>>((acc, s) => {
    (acc[s.component] ??= []).push(s);
    return acc;
  }, {});

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{specs.length} torque specification{specs.length !== 1 ? "s" : ""}</p>
        <button
          onClick={() => downloadCSV(specs)}
          className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
        >
          Download CSV
        </button>
      </div>

      {Object.entries(groups).map(([component, groupSpecs]) => (
        <div key={component} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-2 bg-gray-800/60 border-b border-gray-700">
            <h3 className="text-orange-400 font-semibold text-sm">{component}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-800">
                  <th className="text-left px-4 py-2">Fastener</th>
                  <th className="text-right px-4 py-2">ft-lb</th>
                  <th className="text-right px-4 py-2">Nm</th>
                  <th className="text-left px-4 py-2 hidden sm:table-cell">Notes</th>
                  <th className="text-right px-4 py-2 hidden sm:table-cell">Pg</th>
                </tr>
              </thead>
              <tbody>
                {groupSpecs.map((s, i) => (
                  <tr key={i} className="border-b border-gray-800/60 last:border-0 hover:bg-gray-800/30">
                    <td className="px-4 py-2.5 text-gray-200">{s.fastener}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-orange-300">
                      {formatValue(s.torque_ftlb, s.torque_ftlb_max)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-gray-300">
                      {formatValue(s.torque_nm, s.torque_nm_max)}
                    </td>
                    <td className="px-4 py-2.5 text-gray-500 text-xs hidden sm:table-cell">
                      {s.notes ?? ""}
                    </td>
                    <td className="px-4 py-2.5 text-right text-gray-600 text-xs hidden sm:table-cell">
                      {s.page_ref ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
