/**
 * Auto-configure IP address for React Native development
 * Detects current IP, updates config, and sets up Metro bundler
 */

const os = require('os');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get local IP address
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

// Update env.ts with new IP
function updateEnvFile(newIP) {
  const envPath = path.join(__dirname, '../src/config/env.ts');
  
  try {
    let envContent = fs.readFileSync(envPath, 'utf8');
    
    // Replace IP address in API_URL - try multiple patterns
    const patterns = [
      // Pattern 1: API_URL: 'http://IP:8000/api'
      /(API_URL:\s*['"]http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+\/api['"])/g,
      // Pattern 2: API_URL: "http://IP:8000/api"
      /(API_URL:\s*["']http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+\/api["'])/g,
      // Pattern 3: Any IP in API_URL
      /(API_URL:\s*['"]http:\/\/)(\d+\.\d+\.\d+\.\d+)(:\d+)/g,
    ];
    
    let updated = false;
    for (const pattern of patterns) {
      if (pattern.test(envContent)) {
        envContent = envContent.replace(pattern, `$1${newIP}$3`);
        updated = true;
        break;
      }
    }
    
    if (!updated) {
      // Fallback: replace any IP-like pattern in API_URL line
      const lines = envContent.split('\n');
      const updatedLines = lines.map(line => {
        if (line.includes('API_URL') && line.includes('http://')) {
          return line.replace(/\d+\.\d+\.\d+\.\d+/, newIP);
        }
        return line;
      });
      envContent = updatedLines.join('\n');
    }
    
    fs.writeFileSync(envPath, envContent, 'utf8');
    return true;
  } catch (error) {
    console.error('❌ Error updating env.ts:', error.message);
    return false;
  }
}

// Get connected Android device ID
function getDeviceId() {
  try {
    const output = execSync('adb devices', { encoding: 'utf8' });
    const lines = output.split('\n');
    for (const line of lines) {
      if (line.includes('device') && !line.includes('List') && !line.includes('emulator')) {
        const deviceId = line.split('\t')[0].trim();
        if (deviceId) {
          return deviceId;
        }
      }
    }
    return null;
  } catch (error) {
    return null;
  }
}

// Setup ADB reverse (for USB connections)
function setupADBReverse(deviceId, ip) {
  if (!deviceId) {
    return false;
  }
  
  try {
    console.log('📱 Setting up ADB reverse for USB connection...');
    
    // Remove existing reverse rules
    try {
      execSync(`adb -s ${deviceId} reverse --remove-all`, { encoding: 'utf8', stdio: 'pipe' });
    } catch (e) {
      // Ignore if no rules exist
    }
    
    // Setup reverse for Metro (8081) and API (8000)
    execSync(`adb -s ${deviceId} reverse tcp:8081 tcp:8081`, { encoding: 'utf8', stdio: 'pipe' });
    execSync(`adb -s ${deviceId} reverse tcp:8000 tcp:8000`, { encoding: 'utf8', stdio: 'pipe' });
    
    console.log('✅ ADB reverse configured!');
    console.log('   Phone can now use localhost:8081 (via USB)');
    return true;
  } catch (error) {
    console.log('⚠️  ADB reverse setup failed (phone may not be connected via USB)');
    return false;
  }
}

// Try to configure phone's debug server host (experimental)
function configurePhoneDebugHost(deviceId, ip) {
  if (!deviceId) {
    return false;
  }
  
  try {
    // Method 1: Try to set via React Native DevSettings
    // Note: This may not work on all React Native versions
    try {
      const hostPort = `${ip}:8081`;
      // Use ADB to send a broadcast that React Native might pick up
      execSync(`adb -s ${deviceId} shell settings put global debug_http_host ${hostPort}`, 
        { encoding: 'utf8', stdio: 'pipe' });
      console.log(`📱 Attempted to set phone debug host to ${hostPort}`);
      return true;
    } catch (e) {
      // This method may not work, that's okay
      return false;
    }
  } catch (error) {
    return false;
  }
}

// Main function
function main() {
  console.log('🚀 Auto-Configuring IP for React Native Development');
  console.log('================================================\n');
  
  // Step 1: Detect IP
  console.log('[1/4] Detecting current IP address...');
  const ip = getLocalIP();
  if (ip === 'localhost') {
    console.error('❌ Could not detect IP address. Please check your network connection.');
    process.exit(1);
  }
  console.log(`✅ Detected IP: ${ip}\n`);
  
  // Step 2: Update env.ts
  console.log('[2/4] Updating API configuration...');
  if (updateEnvFile(ip)) {
    console.log(`✅ Updated API_URL to http://${ip}:8000/api\n`);
  } else {
    console.error('❌ Failed to update env.ts');
    process.exit(1);
  }
  
  // Step 3: Check for connected device
  console.log('[3/4] Checking for connected Android device...');
  const deviceId = getDeviceId();
  if (deviceId) {
    console.log(`✅ Device found: ${deviceId}\n`);
    
    // Setup ADB reverse (works for USB connections)
    setupADBReverse(deviceId, ip);
    
    // Try to configure phone's debug host (may not work, but worth trying)
    configurePhoneDebugHost(deviceId, ip);
  } else {
    console.log('⚠️  No Android device found (phone may not be connected via USB)\n');
  }
  
  // Step 4: Display configuration
  console.log('[4/4] Configuration Complete!');
  console.log('================================================\n');
  console.log('📋 Configuration:');
  console.log(`   Backend API: http://${ip}:8000/api`);
  console.log(`   Metro Server: http://${ip}:8081`);
  console.log('\n📱 Phone Configuration:');
  
  if (deviceId) {
    console.log('   ✅ USB Connection: ADB reverse is configured');
    console.log('   📝 WiFi Connection: You may still need to configure debug host manually');
    console.log('\n   To configure debug host on phone:');
    console.log('   1. Shake phone (or press menu button)');
    console.log('   2. Select "Settings"');
    console.log(`   3. Select "Debug server host & port for device"`);
    console.log(`   4. Enter: ${ip}:8081`);
    console.log('   5. Reload app');
  } else {
    console.log('   📝 Configure debug host on phone:');
    console.log('   1. Shake phone (or press menu button)');
    console.log('   2. Select "Settings"');
    console.log(`   3. Select "Debug server host & port for device"`);
    console.log(`   4. Enter: ${ip}:8081`);
    console.log('   5. Reload app');
  }
  
  console.log('\n🚀 Next Steps:');
  console.log('   1. Start Metro: npm run start (or START_METRO_AUTO.bat)');
  console.log('   2. Start Backend: cd backend && python run.py');
  console.log('   3. Configure phone (if not using USB)');
  console.log('   4. Reload app on phone');
  console.log('\n================================================\n');
  
  // Return IP for use in other scripts
  return ip;
}

// Run if called directly
if (require.main === module) {
  const ip = main();
  // Export IP for use in other scripts
  process.env.DETECTED_IP = ip;
}

module.exports = { getLocalIP, updateEnvFile, setupADBReverse, configurePhoneDebugHost };









