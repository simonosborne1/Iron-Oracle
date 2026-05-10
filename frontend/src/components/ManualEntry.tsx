import { useState } from "react";

interface Props {
  onSubmit: (make: string, model: string, serial: string) => void;
}

export default function ManualEntry({ onSubmit }: Props) {
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [serial, setSerial] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(make.trim(), model.trim(), serial.trim());
  }

  const inputClass =
    "bg-gray-800 text-white rounded-xl px-4 py-3 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-orange-500 w-full";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label className="text-sm text-gray-400">Make</label>
        <input
          value={make}
          onChange={(e) => setMake(e.target.value)}
          placeholder="e.g. Skyjack"
          className={inputClass}
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm text-gray-400">Model</label>
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="e.g. SJ1256THS"
          className={inputClass}
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm text-gray-400">Serial Number</label>
        <input
          value={serial}
          onChange={(e) => setSerial(e.target.value)}
          placeholder="e.g. 87410194"
          className={inputClass}
        />
      </div>
      <button
        type="submit"
        disabled={!make.trim() && !model.trim() && !serial.trim()}
        className="bg-orange-500 hover:bg-orange-600 active:bg-orange-700 disabled:opacity-40 text-white font-semibold py-4 rounded-xl text-lg transition-colors"
      >
        Find Manuals
      </button>
    </form>
  );
}
