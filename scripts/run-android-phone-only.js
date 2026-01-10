/**
 * Run Android on Physical Device Only
 * Prevents emulator from opening
 */
const { execSync } = require('child_process');
const os = require('os');

console.log('============================================================');
console.log('Installing on Physical Device ONLY');
console.log('============================================================\n');

// Step 1: Kill all emulators
console.log('[1/5] Killing all emulators...');
try {
  if (os.platform() === 'win32') {
    execSync('adb emu kill', { stdio: 'ignore' });
    execSync('taskkill /F /IM qemu-system-x86_64.exe', { stdio: 'ignore' });
    execSync('taskkill /F /IM emulator.exe', { stdio: 'ignore' });
  } else {
    execSync('adb emu kill', { stdio: 'ignore' });
    execSync('pkill -f qemu', { stdio: 'ignore' });
  }
} catch (e) {
  // Ignore errors if emulators not running
}
console.log('Done!\n');

// Step 2: Restart ADB
console.log('[2/5] Restarting ADB...');
try {
  execSync('adb kill-server', { stdio: 'ignore' });
  // Wait a moment for ADB to fully stop
  if (os.platform() === 'win32') {
    execSync('timeout /t 2 /nobreak >nul', { stdio: 'ignore' });
  } else {
    execSync('sleep 2', { stdio: 'ignore' });
  }
  execSync('adb start-server', { stdio: 'pipe' });
  // Wait for devices to reconnect
  if (os.platform() === 'win32') {
    execSync('timeout /t 3 /nobreak >nul', { stdio: 'ignore' });
  } else {
    execSync('sleep 3', { stdio: 'ignore' });
  }
} catch (e) {
  console.error('Error restarting ADB:', e.message);
  process.exit(1);
}
console.log('Done!\n');

// Step 3: Get physical device (with retry)
console.log('[3/5] Finding your phone...');
let deviceId = null;
const maxRetries = 3;

for (let attempt = 1; attempt <= maxRetries; attempt++) {
  try {
    const devicesOutput = execSync('adb devices', { encoding: 'utf8' });
    const lines = devicesOutput.split('\n');
    
    for (const line of lines) {
      if (line.includes('device') && !line.includes('emulator') && !line.includes('List')) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 2 && parts[1] === 'device') {
          deviceId = parts[0];
          break;
        }
      }
    }
    
    if (deviceId) {
      // Verify device is still connected
      try {
        execSync(`adb -s ${deviceId} shell echo test`, { stdio: 'ignore' });
        break; // Device is valid and connected
      } catch (e) {
        console.log(`Device ${deviceId} found but not responding, retrying...`);
        deviceId = null;
        if (attempt < maxRetries) {
          if (os.platform() === 'win32') {
            execSync('timeout /t 2 /nobreak >nul', { stdio: 'ignore' });
          } else {
            execSync('sleep 2', { stdio: 'ignore' });
          }
        }
      }
    } else if (attempt < maxRetries) {
      console.log(`No device found, retrying... (${attempt}/${maxRetries})`);
      if (os.platform() === 'win32') {
        execSync('timeout /t 2 /nobreak >nul', { stdio: 'ignore' });
      } else {
        execSync('sleep 2', { stdio: 'ignore' });
      }
    }
  } catch (e) {
    if (attempt < maxRetries) {
      console.log(`Error checking devices, retrying... (${attempt}/${maxRetries})`);
      if (os.platform() === 'win32') {
        execSync('timeout /t 2 /nobreak >nul', { stdio: 'ignore' });
      } else {
        execSync('sleep 2', { stdio: 'ignore' });
      }
    } else {
      console.error('Error checking devices:', e.message);
    }
  }
}

if (!deviceId) {
  console.error('\n❌ ERROR: No physical device found!');
  console.error('\nPlease check:');
  console.error('1. Phone is connected via USB');
  console.error('2. USB Debugging is enabled');
  console.error('3. Computer is authorized (check phone for popup)');
  console.error('4. Phone is unlocked');
  console.error('5. USB cable is working properly');
  console.error('\nCurrent devices:');
  try {
    execSync('adb devices', { stdio: 'inherit' });
  } catch (e) {}
  console.error('\nTry:');
  console.error('1. Unplug and replug USB cable');
  console.error('2. Run: adb kill-server && adb start-server');
  console.error('3. Check phone for authorization popup');
  process.exit(1);
}

console.log(`✅ Phone found: ${deviceId}\n`);

// Step 4: Verify device connection and setup ADB reverse
console.log('[4/5] Verifying device connection and setting up port forwarding...');
try {
  // Verify device is still connected
  execSync(`adb -s ${deviceId} shell echo "Device connected"`, { stdio: 'ignore' });
  
  // Remove existing reverse rules
  try {
    execSync(`adb -s ${deviceId} reverse --remove-all`, { stdio: 'ignore' });
  } catch (e) {
    // Ignore if no rules exist
  }
  
  // Setup reverse for Metro (8081) and API (8000)
  execSync(`adb -s ${deviceId} reverse tcp:8081 tcp:8081`, { stdio: 'pipe' });
  execSync(`adb -s ${deviceId} reverse tcp:8000 tcp:8000`, { stdio: 'pipe' });
  console.log('✅ Port forwarding configured');
} catch (e) {
  console.error('❌ Error: Device connection lost or port forwarding failed');
  console.error('Please reconnect your phone and try again');
  console.error(`Error: ${e.message}`);
  process.exit(1);
}
console.log('Done!\n');

// Step 5: Final device verification and install
console.log('[5/5] Final verification and installing on your phone...');

// One final check that device is still connected
try {
  execSync(`adb -s ${deviceId} shell echo "Ready"`, { stdio: 'ignore' });
} catch (e) {
  console.error('\n❌ ERROR: Device disconnected!');
  console.error(`Device ${deviceId} is no longer available.`);
  console.error('\nPlease:');
  console.error('1. Check USB connection');
  console.error('2. Unlock your phone');
  console.error('3. Re-run this script');
  process.exit(1);
}

console.log(`Device: ${deviceId}`);
console.log('(This will NOT open emulator)');
console.log('\n⚠️  IMPORTANT: Keep your phone unlocked and connected during installation!');
console.log('============================================================\n');

try {
  execSync(`npx react-native run-android --deviceId=${deviceId}`, {
    stdio: 'inherit',
    cwd: process.cwd()
  });
  console.log('\n✅ Installation completed successfully!');
} catch (e) {
  console.error('\n❌ Installation failed.');
  console.error('\nTroubleshooting:');
  console.error('1. Make sure phone is unlocked');
  console.error('2. Check USB cable connection');
  console.error('3. Try: adb kill-server && adb start-server');
  console.error('4. Verify device: adb devices');
  console.error('5. Try uninstalling app first: adb uninstall com.GharMitra');
  process.exit(1);
}

