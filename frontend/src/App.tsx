import { useState } from "react";
import { useAppFlow } from "./hooks/useAppFlow";
import CameraCapture from "./components/CameraCapture";
import ManualEntry from "./components/ManualEntry";
import MachineCard from "./components/MachineCard";
import ManualList from "./components/ManualList";
import TorqueTable from "./components/TorqueTable";
import ProgressIndicator from "./components/ProgressIndicator";
import ErrorBanner from "./components/ErrorBanner";
import LoadingSpinner from "./components/LoadingSpinner";

export default function App() {
  const {
    step, error, machine, manuals, manualStatus, specs, activeManualUrl, rawOcr,
    runScan, enterManually, runManualSearch, runTorqueExtraction, reset,
  } = useAppFlow();
  const [entryMode, setEntryMode] = useState<"scan" | "manual">("scan");

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="px-4 pt-6 pb-2 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-orange-400 tracking-tight">Iron Oracle</h1>
          <p className="text-xs text-gray-500">Heavy Equipment Manual Finder</p>
        </div>
        {step !== "idle" && (
          <button
            onClick={reset}
            className="text-sm px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg"
          >
            New Scan
          </button>
        )}
      </header>

      <ProgressIndicator step={step} />

      <main className="flex-1 px-4 pb-8 flex flex-col gap-4 max-w-lg mx-auto w-full">
        {error && <ErrorBanner message={error} onDismiss={() => {}} />}

        {/* Step 0 — Scan or Manual Entry */}
        {(step === "idle" || step === "scanning") && (
          <div className="flex flex-col gap-4">
            {step === "idle" && (
              <div className="flex rounded-xl overflow-hidden border border-gray-800">
                <button
                  onClick={() => setEntryMode("scan")}
                  className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                    entryMode === "scan"
                      ? "bg-orange-500 text-white"
                      : "bg-gray-900 text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Scan Plate
                </button>
                <button
                  onClick={() => setEntryMode("manual")}
                  className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                    entryMode === "manual"
                      ? "bg-orange-500 text-white"
                      : "bg-gray-900 text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Enter Manually
                </button>
              </div>
            )}
            {entryMode === "scan" || step === "scanning" ? (
              <CameraCapture onCapture={runScan} isProcessing={step === "scanning"} />
            ) : (
              <ManualEntry onSubmit={enterManually} />
            )}
          </div>
        )}

        {/* Step 1 — Machine identified */}
        {machine && step !== "scanning" && (
          <MachineCard
            machine={machine}
            onFindManuals={runManualSearch}
            loading={step === "searching"}
          />
        )}

        {/* OCR debug panel */}
        {rawOcr && step !== "scanning" && (
          <details className="bg-gray-900 rounded-xl p-3">
            <summary className="text-xs text-gray-500 cursor-pointer select-none">Raw OCR text (tap to expand)</summary>
            <pre className="text-xs text-gray-400 mt-2 whitespace-pre-wrap break-all">{rawOcr}</pre>
          </details>
        )}

        {/* Step 2 — Searching */}
        {step === "searching" && <LoadingSpinner label="Searching for manuals online…" />}

        {/* Step 2 — Manuals found */}
        {(step === "manuals_done" || step === "extracting" || step === "specs_done") && machine && (
          <ManualList
            manuals={manuals}
            status={manualStatus}
            machine={machine}
            onExtractTorque={runTorqueExtraction}
            extractingUrl={step === "extracting" ? activeManualUrl : null}
          />
        )}

        {/* Step 3 — Extracting */}
        {step === "extracting" && <LoadingSpinner label="Extracting torque specs from PDF…" />}

        {/* Step 3 — Specs */}
        {step === "specs_done" && <TorqueTable specs={specs} />}
      </main>
    </div>
  );
}
