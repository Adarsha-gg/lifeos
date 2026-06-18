const LIFEOS_CAPTURE_URL = "http://127.0.0.1:8787/research/capture-api";

async function activeTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function setBadge(text, color) {
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 1800);
}

async function captureCurrentTab() {
  const tab = await activeTab();
  if (!tab || !tab.url) {
    await setBadge("NO", "#ff2b2b");
    return;
  }

  const payload = new URLSearchParams({
    kind: "source",
    text: `${tab.title || "Untitled"} — ${tab.url}`
  });

  try {
    const res = await fetch(LIFEOS_CAPTURE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString()
    });
    if (!res.ok) throw new Error(`LifeOS returned ${res.status}`);
    await setBadge("OK", "#39ff88");
  } catch (err) {
    console.error("LifeOS capture failed", err);
    await setBadge("ERR", "#ff2b2b");
  }
}

chrome.commands.onCommand.addListener((command) => {
  if (command === "capture-tab") captureCurrentTab();
});

chrome.action.onClicked.addListener(() => captureCurrentTab());
