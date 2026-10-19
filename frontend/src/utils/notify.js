/**
 * Central place for user-facing feedback. The prototype uses native browser
 * dialogs; replace these with a toast/modal system without touching call sites.
 */
export function notify(message) {
  window.alert(message);
}

export function confirmAction(message) {
  return window.confirm(message);
}

export async function copyToClipboard(text) {
  try {
    await navigator.clipboard?.writeText(text);
    return true;
  } catch {
    return false;
  }
}
