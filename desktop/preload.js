/**
 * Electron Preload Script
 * Exposes safe APIs to renderer process
 */
const { contextBridge } = require('electron');

// Expose protected methods that allow the renderer process
// to use the APIs without exposing the entire Node.js API
contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,
  isDesktop: true,
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron,
  },
});

