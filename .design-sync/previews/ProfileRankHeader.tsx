import { ProfileRankHeader } from "lifeos-ds";

export function Learner() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ProfileRankHeader
        name="Adarsha"
        role="learner"
        level={5}
        rankTitle="Apprentice Cartographer"
        tier="gold"
        xp={320}
        xpToNext={500}
        streak={7}
        persistence="local-only"
      />
    </div>
  );
}

export function CloudSynced() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ProfileRankHeader
        name="Mira"
        role="learner"
        level={11}
        rankTitle="Journeyman of Systems"
        tier="silver"
        xp={140}
        xpToNext={650}
        streak={23}
        persistence="cloud-configured"
      />
    </div>
  );
}

export function Teacher() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ProfileRankHeader
        name="Dr. Osei"
        role="teacher"
        level={18}
        rankTitle="Mentor of the Guild"
        tier="gold"
        xp={500}
        xpToNext={900}
        persistence="teacher-mode"
      />
    </div>
  );
}
