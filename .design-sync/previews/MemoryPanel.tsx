import { MemoryPanel } from "lifeos-ds";

export function LocalOnly() {
  return (
    <div style={{ maxWidth: 480 }}>
      <MemoryPanel cloud="not-configured" syncCode="LIFEOS-7QF2-9KD1-AAC8" />
    </div>
  );
}

export function CloudConfigured() {
  return (
    <div style={{ maxWidth: 480 }}>
      <MemoryPanel cloud="configured" syncCode="LIFEOS-7QF2-9KD1-AAC8" />
    </div>
  );
}
