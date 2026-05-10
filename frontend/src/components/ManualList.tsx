import type { ManualResult, MachineIdentity } from "../types";

interface Props {
  manuals: ManualResult[];
  status: string;
  machine: MachineIdentity;
  onExtractTorque: (url: string) => void;
  extractingUrl: string | null;
}

const TYPE_COLOURS: Record<string, string> = {
  service:  "bg-blue-900/60 text-blue-300 border-blue-700",
  parts:    "bg-purple-900/60 text-purple-300 border-purple-700",
  operator: "bg-green-900/60 text-green-300 border-green-700",
  unknown:  "bg-gray-800 text-gray-400 border-gray-700",
};

function TypeBadge({ type }: { type: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded border capitalize ${TYPE_COLOURS[type] ?? TYPE_COLOURS.unknown}`}>
      {type}
    </span>
  );
}

export default function ManualList({ manuals, status, machine, onExtractTorque, extractingUrl }: Props) {
  if (status === "no_results") {
    const query = encodeURIComponent(`${machine.make} ${machine.model} service manual`);
    return (
      <div className="text-center py-8 flex flex-col gap-4">
        <p className="text-gray-400">No manuals found automatically.</p>
        <a
          href={`https://www.google.com/search?q=${query}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-4 py-2 bg-gray-800 hover:bg-gray-700 text-orange-400 rounded-lg text-sm"
        >
          Search Google manually →
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-gray-500">{manuals.length} manual{manuals.length !== 1 ? "s" : ""} found</p>
      {manuals.map((m) => (
        <div key={m.url} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-start gap-2">
            <TypeBadge type={m.manual_type} />
            {m.source === "portal" && (
              <span className="text-xs px-2 py-0.5 rounded border bg-orange-900/40 text-orange-300 border-orange-800">
                official
              </span>
            )}
          </div>
          <p className="text-gray-200 text-sm leading-snug">{m.title}</p>
          <div className="flex gap-2 flex-wrap">
            <a
              href={m.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
            >
              Download PDF
            </a>
            {(m.manual_type === "service" || m.manual_type === "unknown") && (
              <button
                onClick={() => onExtractTorque(m.url)}
                disabled={extractingUrl === m.url}
                className="flex-1 py-2 bg-orange-500/20 hover:bg-orange-500/30 disabled:opacity-50 text-orange-300 border border-orange-700 rounded-lg text-sm transition-colors"
              >
                {extractingUrl === m.url ? "Extracting…" : "Extract Torque Specs"}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
