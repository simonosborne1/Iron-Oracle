import { useState, useCallback } from "react";
import type { AppStep, MachineIdentity, ManualResult, TorqueSpec } from "../types";
import { scanPlate, getManuals, getTorque } from "../api";

export function useAppFlow() {
  const [step, setStep] = useState<AppStep>("idle");
  const [error, setError] = useState<string | null>(null);
  const [machine, setMachine] = useState<MachineIdentity | null>(null);
  const [manuals, setManuals] = useState<ManualResult[]>([]);
  const [manualStatus, setManualStatus] = useState<string>("");
  const [specs, setSpecs] = useState<TorqueSpec[]>([]);
  const [activeManualUrl, setActiveManualUrl] = useState<string | null>(null);
  const [rawOcr, setRawOcr] = useState<string | null>(null);

  const runScan = useCallback(async (blob: Blob) => {
    setError(null);
    setStep("scanning");
    try {
      const res = await scanPlate(blob);
      setRawOcr(res.raw_ocr ?? null);
      setMachine(res.machine);
      setStep("scan_done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Scan failed");
      setStep("idle");
    }
  }, []);

  // Accepts corrected make/model/serial from the editable MachineCard
  const runManualSearch = useCallback(async (
    make: string, model: string, serial: string
  ) => {
    setError(null);
    const updated: MachineIdentity = {
      make: make || null,
      model: model || null,
      serial_number: serial || null,
      year: machine?.year ?? null,
      capacity: machine?.capacity ?? null,
      voltage: machine?.voltage ?? null,
      other_ids: machine?.other_ids ?? null,
      confidence: machine?.confidence ?? 1.0,
      notes: machine?.notes ?? null,
    };
    setMachine(updated);
    setStep("searching");
    try {
      const res = await getManuals(updated);
      setManuals(res.manuals);
      setManualStatus(res.search_status);
      setStep("manuals_done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Manual search failed");
      setStep("scan_done");
    }
  }, [machine]);

  // Manual entry goes straight to search — no intermediate confirmation step
  const enterManually = useCallback(async (make: string, model: string, serial: string) => {
    setError(null);
    const newMachine: MachineIdentity = {
      make: make || null,
      model: model || null,
      serial_number: serial || null,
      year: null,
      capacity: null,
      voltage: null,
      other_ids: null,
      confidence: 1.0,
      notes: "Manually entered",
    };
    setMachine(newMachine);
    setStep("searching");
    try {
      const res = await getManuals(newMachine);
      setManuals(res.manuals);
      setManualStatus(res.search_status);
      setStep("manuals_done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Manual search failed");
      setStep("idle");
    }
  }, []);

  const runTorqueExtraction = useCallback(async (manualUrl: string) => {
    if (!machine) return;
    setError(null);
    setActiveManualUrl(manualUrl);
    setStep("extracting");
    try {
      const res = await getTorque(manualUrl, machine);
      setSpecs(res.specs);
      setStep("specs_done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Torque extraction failed");
      setStep("manuals_done");
    }
  }, [machine]);

  const reset = useCallback(() => {
    setStep("idle");
    setError(null);
    setMachine(null);
    setManuals([]);
    setSpecs([]);
    setActiveManualUrl(null);
    setRawOcr(null);
  }, []);

  return {
    step, error, machine, manuals, manualStatus, specs, activeManualUrl, rawOcr,
    runScan, enterManually, runManualSearch, runTorqueExtraction, reset,
  };
}
