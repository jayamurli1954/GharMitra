/**
 * Electron Main Process
 * GharMitra Desktop Application
 */
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    show: false, // Don't show until ready
  });

  // Load app
  if (isDev) {
    mainWindow.loadURL('http://localhost:3001');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../web/dist/index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Create application menu
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          },
        },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About GharMitra',
          click: () => {
            // Show about dialog
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function checkBackendRunning() {
  try {
    const http = require('http');
    return new Promise((resolve) => {
      const req = http.get('http://localhost:8001/health', { timeout: 2000 }, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  } catch (error) {
    return false;
  }
}

function startBackend() {
  const backendPath = path.join(__dirname, '../backend');
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

  // Check if backend is already running
  checkBackendRunning().then((isRunning) => {
    if (isRunning) {
      console.log('Backend is already running on port 8001. Using existing instance.');
      return;
    }

    console.log('Starting backend server...');
    console.log(`Backend path: ${backendPath}`);
    console.log(`Python command: ${pythonCmd}`);

    backendProcess = spawn(pythonCmd, [
      '-m', 'uvicorn',
      'app.main:app',
      '--host', '127.0.0.1',
      '--port', '8001',
    ], {
      cwd: backendPath,
      stdio: 'pipe',
      shell: process.platform === 'win32',
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      const errorStr = data.toString();
      // Check for port already in use error
      if (errorStr.includes('10048') || errorStr.includes('address already in use')) {
        console.log('Backend port 8001 is already in use. Using existing backend instance.');
        backendProcess = null; // Don't treat this as our process
      } else {
        console.error(`Backend Error: ${data}`);
      }
    });

    backendProcess.on('close', (code) => {
      if (backendProcess) { // Only log if it was our process
        console.log(`Backend process exited with code ${code}`);
        if (code !== 0 && code !== null && code !== 1) {
          console.error('Backend process failed to start or crashed');
        }
      }
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      // Show error dialog to user
      if (mainWindow) {
        mainWindow.webContents.send('backend-error', error.message);
      }
    });
  });
}

// App event handlers
app.whenReady().then(async () => {
  // Check if backend is already running
  const isRunning = await checkBackendRunning();
  if (!isRunning) {
    startBackend();
    // Wait a bit for backend to start
    await new Promise(resolve => setTimeout(resolve, 3000));
  } else {
    console.log('Using existing backend instance.');
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

// Handle app termination
process.on('SIGTERM', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
  app.quit();
});


