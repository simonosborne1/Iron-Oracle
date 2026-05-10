export interface MachineIdentity {
  make: string | null;
  model: string | null;
  serial_number: string | null;
  year: number | null;
  capacity: string | null;
  voltage: string | null;
  other_ids: Record<string, string> | null;
  confidence: number;
  notes: string | null;
}

export interface ManualResult {
  title: string;
  url: string;
  manual_type: "service" | "parts" | "operator" | "unknown";
  source: "portal" | "serper";
  file_size_kb: number | null;
}

export interface TorqueSpec {
  component: string;
  fastener: string;
  torque_ftlb: number | null;
  torque_ftlb_max: number | null;
  torque_nm: number | null;
  torque_nm_max: number | null;
  notes: string | null;
  page_ref: number | null;
}

export interface ScanResponse {
  machine: MachineIdentity;
  cached: boolean;
}

export interface ManualsResponse {
  manuals: ManualResult[];
  search_status: string;
  cached: boolean;
}

export interface TorqueResponse {
  specs: TorqueSpec[];
  extraction_method: string;
  spec_count: number;
  cached: boolean;
}

export type AppStep = "idle" | "scanning" | "scan_done" | "searching" | "manuals_done" | "extracting" | "specs_done";
