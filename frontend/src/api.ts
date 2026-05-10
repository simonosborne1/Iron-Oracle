import type { ScanResponse, ManualsResponse, TorqueResponse, MachineIdentity } from "./types";

const BASE = "/api";

export async function scanPlate(imageBlob: Blob): Promise<ScanResponse> {
  const form = new FormData();
  form.append("image", imageBlob, "plate.jpg");
  const res = await fetch(`${BASE}/scan`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail ?? "Scan failed");
  return res.json();
}

export async function getManuals(machine: MachineIdentity): Promise<ManualsResponse> {
  const res = await fetch(`${BASE}/manuals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      make: machine.make ?? "",
      model: machine.model ?? "",
      serial_number: machine.serial_number ?? "",
    }),
  });
  if (!res.ok) throw new Error((await res.json()).detail ?? "Manual search failed");
  return res.json();
}

export async function getTorque(manualUrl: string, machine: MachineIdentity): Promise<TorqueResponse> {
  const res = await fetch(`${BASE}/torque`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      manual_url: manualUrl,
      make: machine.make ?? "",
      model: machine.model ?? "",
    }),
  });
  if (!res.ok) throw new Error((await res.json()).detail ?? "Torque extraction failed");
  return res.json();
}
