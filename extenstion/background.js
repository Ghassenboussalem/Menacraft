// Background service worker for InstaGrab
// Handles messages between popup and content scripts

chrome.runtime.onInstalled.addListener(() => {
  console.log('InstaGrab extension installed');
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getTabInfo') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      sendResponse({ tab: tabs[0] });
    });
    return true;
  }
});
