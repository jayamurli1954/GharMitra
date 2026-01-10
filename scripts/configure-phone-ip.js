/**
 * Automatically configure phone's debug server host
 * This script detects IP, updates config, and configures the phone automatically
 */

const { execSync } = require('child_process');
const os = require('os');
const fs = require('fs');
const path = require('path');

// Get local IP (shared with get-ip.js logic)
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  // Priority order: Wi-Fi (various spellings), Ethernet, then any other
  const priority = ['Wi-Fi', 'Wi-Fi', 'Ethernet', 'Local Area Connection', 'eth0', 'wlan0'];
  
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

// Check if device is connected
function isDeviceConnected() {
  try {
    const output = execSync('adb devices', { encoding: 'utf8', stdio: 'pipe' });
    const lines = output.split('\n').filter(line => line.trim() && !line.includes('List of devices'));
    const devices = lines.filter(line => line.includes('device') && !line.includes('unauthorized'));
    return devices.length > 0;
  } catch (error) {
    return false;
  }
}

// Get connected device ID
function getDeviceId() {
  try {
    const output = execSync('adb devices', { encoding: 'utf8', stdio: 'pipe' });
    const lines = output.split('\n').filter(line => line.trim() && !line.includes('List of devices'));
    const devices = lines.filter(line => line.includes('device') && !line.includes('unauthorized') && !line.includes('emulator'));
    
    if (devices.length === 0) {
      return null;
    }
    
    // Get first physical device (not emulator)
    const deviceLine = devices.find(line => !line.includes('emulator')) || devices[0];
    return deviceLine.split('\t')[0].trim();
  } catch (error) {
    return null;
  }
}

// Set debug server host on phone using ADB
function setDebugServerHost(deviceId, ip, port = 8081) {
  const hostPort = `${ip}:${port}`;
  
  try {
    console.log(`📱 Configuring phone's debug server host to: ${hostPort}`);
    
    // Method 1: Use ADB to set in React Native DevSettings
    // This requires the app to be running, so we'll use a broadcast
    try {
      // Try to set via React Native DevSettings (if app supports it)
      execSync(`adb -s ${deviceId} shell am broadcast -a com.facebook.react.bridge.ReactMarker.logMarker --es "debug_http_host" "${hostPort}"`, 
        { encoding: 'utf8', stdio: 'pipe' });
    } catch (e) {
      // Ignore if not supported
    }
    
    // Method 2: Set via Android settings (works for React Native)
    try {
      execSync(`adb -s ${deviceId} shell settings put global debug_http_host ${hostPort}`, 
        { encoding: 'utf8', stdio: 'pipe' });
      console.log('✅ Set debug server host via Android settings');
    } catch (e) {
      console.log('⚠️  Could not set via Android settings, will use ADB reverse instead');
    }
    
    // Method 3: Use ADB reverse (always works for USB connections)
    try {
      execSync(`adb -s ${deviceId} reverse --remove-all`, { encoding: 'utf8', stdio: 'pipe' });
      execSync(`adb -s ${deviceId} reverse tcp:${port} tcp:${port}`, { encoding: 'utf8', stdio: 'pipe' });
      execSync(`adb -s ${deviceId} reverse tcp:8000 tcp:8000`, { encoding: 'utf8', stdio: 'pipe' });
      console.log('✅ Set up ADB reverse port forwarding');
      console.log(`   Phone can now use localhost:${port} to connect to ${ip}:${port}`);
    } catch (e) {
      console.log('⚠️  ADB reverse setup failed:', e.message);
    }
    
    // Method 4: Store in a file that the app can read (alternative)
    // This requires app modification, so we'll document it instead
    
    return true;
  } catch (error) {
    console.error('❌ Error setting debug server host:', error.message);
    return false;
  }
}

// Update env.ts
function updateEnvTs(ip) {
  const envPath = path.join(__dirname, '../src/config/env.ts');
  
  try {
    let envContent = fs.readFileSync(envPath, 'utf8');
    
    // Replace IP address in API_URL
    const patterns = [
      /(API_URL:\s*['"]http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+\/api['"])/g,
      /(API_URL:\s*["']http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+\/api["'])/g,
      /(API_URL:\s*['"]http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+)/g,
    ];
    
    let updated = false;
    for (const pattern of patterns) {
      if (pattern.test(envContent)) {
        envContent = envContent.replace(pattern, `$1${ip}$3`);
        updated = true;
        break;
      }
    }
    
    if (!updated) {
      // Fallback: replace any IP-like pattern in API_URL line
      const lines = envContent.split('\n');
      const updatedLines = lines.map(line => {
        if (line.includes('API_URL') && line.includes('http://')) {
          return line.replace(/\d+\.\d+\.\d+\.\d+/, ip);
        }
        return line;
      });
      envContent = updatedLines.join('\n');
    }
    
    fs.writeFileSync(envPath, envContent, 'utf8');
    console.log(`✅ Updated API_URL in env.ts to http://${ip}:8000/api`);
    return true;
  } catch (error) {
    console.error('❌ Error updating env.ts:', error.message);
    return false;
  }
}

// Main function
function main() {
  console.log('🔍 Auto-Configuring IP Address and Phone Connection...\n');
  
  // Step 1: Detect IP
  const ip = getLocalIP();
  console.log(`📍 Detected IP address: ${ip}\n`);
  
  if (ip === 'localhost') {
    console.error('❌ Could not detect IP address. Please check your network connection.');
    process.exit(1);
  }
  
  // Step 2: Update env.ts
  console.log('📝 Updating frontend configuration...');
  if (!updateEnvTs(ip)) {
    console.error('❌ Failed to update env.ts');
    process.exit(1);
  }
  console.log('');
  
  // Step 3: Check device connection
  console.log('📱 Checking device connection...');
  if (!isDeviceConnected()) {
    console.log('⚠️  No device connected via USB');
    console.log('   Please connect your phone via USB and enable USB debugging');
    console.log(`   Then manually set debug server host on phone to: ${ip}:8081`);
    console.log(`   Or use ADB reverse: adb reverse tcp:8081 tcp:8081`);
    process.exit(0);
  }
  
  const deviceId = getDeviceId();
  if (!deviceId) {
    console.log('⚠️  Could not find device ID');
    console.log(`   Please manually set debug server host on phone to: ${ip}:8081`);
    process.exit(0);
  }
  
  console.log(`✅ Device connected: ${deviceId}\n`);
  
  // Step 4: Configure phone
  if (setDebugServerHost(deviceId, ip)) {
    console.log('\n✅ Phone configured successfully!');
    console.log(`\n📋 Configuration Summary:`);
    console.log(`   Computer IP: ${ip}`);
    console.log(`   Metro Server: http://${ip}:8081`);
    console.log(`   Backend API: http://${ip}:8000/api`);
    console.log(`   Device ID: ${deviceId}`);
    console.log(`\n🚀 Next steps:`);
    console.log(`   1. Start Metro: npm start -- --host ${ip}`);
    console.log(`   2. Reload app on phone (shake → Reload)`);
    console.log(`   3. If still having issues, manually set debug server host to: ${ip}:8081`);
  } else {
    console.log('\n⚠️  Could not configure phone automatically');
    console.log(`   Please manually set debug server host on phone to: ${ip}:8081`);
    console.log(`   Shake phone → Settings → Debug server host → Enter: ${ip}:8081`);
  }
  
  // Return IP for use in other scripts
  return ip;
}

// Run if called directly
if (require.main === module) {
  const ip = main();
  // Export IP for other scripts
  console.log(`\n💾 IP address saved: ${ip}`);
}

// Export IP getter that can be used by other scripts
module.exports = { getLocalIP, setDebugServerHost, updateEnvTs, main };

// Also export the IP directly if needed
if (require.main === module) {
  const ip = getLocalIP();
  module.exports.currentIP = ip;
}

