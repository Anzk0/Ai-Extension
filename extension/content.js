let overlayVisible = false;
let overlayContainer = null;

function createOverlay() {
  overlayContainer = document.createElement('div');
  overlayContainer.id = 'study-ai-overlay-root';
  overlayContainer.style.cssText = [
    'position: fixed',
    'bottom: 20px',
    'right: 20px',
    'z-index: 2147483647',
    'display: flex',
    'flex-direction: column',
    'align-items: flex-end',
    'pointer-events: none'
  ].join(';');

  const iframe = document.createElement('iframe');
  iframe.id = 'study-ai-iframe';
  iframe.src = chrome.runtime.getURL('overlay/overlay.html');
  iframe.style.cssText = [
    'width: 380px',
    'height: 520px',
    'border: none',
    'border-radius: 12px',
    'box-shadow: 0 8px 32px rgba(0,0,0,0.45)',
    'pointer-events: all'
  ].join(';');

  overlayContainer.appendChild(iframe);
  document.body.appendChild(overlayContainer);
}

function removeOverlay() {
  if (overlayContainer) {
    overlayContainer.remove();
    overlayContainer = null;
  }
}

function minimiseOverlay() {
  const iframe = overlayContainer && overlayContainer.querySelector('iframe');
  if (!iframe) return;
  iframe.style.width = '48px';
  iframe.style.height = '48px';
  iframe.style.borderRadius = '50%';
  iframe.contentWindow.postMessage({ type: 'SET_MINIMISED', value: true }, '*');
}

function expandOverlay() {
  const iframe = overlayContainer && overlayContainer.querySelector('iframe');
  if (!iframe) return;
  iframe.style.width = '380px';
  iframe.style.height = '520px';
  iframe.style.borderRadius = '12px';
  iframe.contentWindow.postMessage({ type: 'SET_MINIMISED', value: false }, '*');
}

// Messages from toolbar icon click (background.js)
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'TOGGLE_OVERLAY') {
    if (overlayVisible) {
      removeOverlay();
      overlayVisible = false;
    } else {
      createOverlay();
      overlayVisible = true;
    }
  }
});

// Messages from iframe (overlay.js → postMessage to parent)
window.addEventListener('message', (event) => {
  if (!event.data) return;
  if (event.data.type === 'MINIMISE_OVERLAY') minimiseOverlay();
  if (event.data.type === 'EXPAND_OVERLAY') expandOverlay();
  if (event.data.type === 'CLOSE_OVERLAY') {
    removeOverlay();
    overlayVisible = false;
  }
});

// Send highlighted text to the overlay iframe
document.addEventListener('mouseup', () => {
  if (!overlayVisible || !overlayContainer) return;
  const selected = window.getSelection();
  const text = selected ? selected.toString().trim() : '';
  if (!text) return;
  const iframe = overlayContainer.querySelector('iframe');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage({ type: 'HIGHLIGHTED_TEXT', text }, '*');
  }
});
