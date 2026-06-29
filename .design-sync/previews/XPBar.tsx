import { XPBar } from "lifeos-ds";

export function Default() {
  return (
    <div style={{ maxWidth: 420 }}>
      <XPBar current={320} next={500} label="XP to next rank" />
    </div>
  );
}

export function NearlyThere() {
  return (
    <div style={{ maxWidth: 420 }}>
      <XPBar current={470} next={500} label="Almost level 5" />
    </div>
  );
}

export function Compact() {
  return (
    <div style={{ maxWidth: 320 }}>
      <XPBar current={120} next={400} size="sm" showValue={false} />
    </div>
  );
}
