/**
 * Update IP address in env.ts automatically
 */
const fs = require('fs');
const path = require('path');
const { getLocalIP } = require('./get-ip');

const envPath = path.join(__dirname, '../src/config/env.ts');
const newIP = getLocalIP();

try {
  // Read current env.ts
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

  if (updated) {
    fs.writeFileSync(envPath, envContent, 'utf8');
    console.log(`✅ Updated API_URL to http://${newIP}:8000/api`);
  } else {
    // Fallback: replace any IP-like pattern in API_URL line
    const lines = envContent.split('\n');
    const updatedLines = lines.map(line => {
      if (line.includes('API_URL') && line.includes('http://')) {
        return line.replace(/\d+\.\d+\.\d+\.\d+/, newIP);
      }
      return line;
    });
    
    if (updatedLines.join('\n') !== envContent) {
      fs.writeFileSync(envPath, updatedLines.join('\n'), 'utf8');
      console.log(`✅ Updated API_URL to http://${newIP}:8000/api`);
    } else {
      console.log('⚠️  Could not find API_URL pattern to update');
      console.log('Please check src/config/env.ts manually');
    }
  }

  console.log(`📍 Detected IP: ${newIP}`);
} catch (error) {
  console.error('❌ Error updating env.ts:', error.message);
  process.exit(1);
}

module.exports = { newIP };

