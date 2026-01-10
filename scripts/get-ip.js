/**
 * Auto-detect IP address script
 * Finds the active network interface IP address
 */
const os = require('os');

function getLocalIP() {
  const interfaces = os.networkInterfaces();
  
  // Priority order: WiFi, Ethernet, then any other
  const priority = ['Wi-Fi', 'Ethernet', 'Local Area Connection', 'eth0', 'wlan0'];
  
  // Try priority interfaces first
  for (const ifaceName of priority) {
    const iface = interfaces[ifaceName];
    if (iface) {
      for (const addr of iface) {
        if (addr.family === 'IPv4' && !addr.internal) {
          return addr.address;
        }
      }
    }
  }
  
  // Fallback: find any non-internal IPv4 address
  for (const ifaceName in interfaces) {
    const iface = interfaces[ifaceName];
    for (const addr of iface) {
      if (addr.family === 'IPv4' && !addr.internal) {
        return addr.address;
      }
    }
  }
  
  return 'localhost';
}

const ip = getLocalIP();
console.log(ip);
module.exports = { getLocalIP };

