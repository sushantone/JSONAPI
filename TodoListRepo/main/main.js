const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const { app, BrowserWindow, ipcMain, screen, Tray, Menu, globalShortcut, nativeImage } = require('electron');

const appId = process.env.REACT_APP_PROTOCOL_ID || 'mytodo'; // fallback if env is missing
let mainWindow;
let deepLinkUrl = null;
let tray;
let store;

// Ensure single instance
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, argv) => {
    const url = argv.find(arg => arg.startsWith(`${appId}://`));
    if (url && mainWindow) {
      const code = extractCode(url);
      if (code) {
        mainWindow.webContents.send('auth-code-received', code);
      }
      mainWindow.focus();
    }
  });

  app.on('ready', async () => {
    const { default: Store } = await import('electron-store');
    store = new Store();
    app.setAsDefaultProtocolClient(appId);
    // Capture deep link on first launch
    const args = process.argv;
    deepLinkUrl = args.find(arg => arg.startsWith(`${appId}://`));

    const win = createWindow();
    configureTray(app, win)
  });



}

function extractCode() {
  try {
    const parsed = new URL(deepLinkUrl);
    const code = parsed.searchParams.get('code');
    return code || null;
  } catch (err) {
    console.error('Failed to parse deep link:', err);
    return null;
  }
}


function configureTray() {

  const iconPath = path.join(__dirname, 'assets', 'tick.png')
  const trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  tray = new Tray(trayIcon);

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show App', click: () => mainWindow.show() },
    { label: 'Hide App', click: () => mainWindow.hide() },
    { label: 'Quit', click: () => app.quit() }
  ]);

  tray.setToolTip('MS-TODO Client');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    //tray.popUpContextMenu()
  });

  tray.on('right-click', () => {
    tray.popUpContextMenu();
  });



  const toggleWindow = () => mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();

  globalShortcut.register('CommandOrControl+Alt+Z', () => {
    toggleWindow();
  });

  const debounce = (fn, delay) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  };

  const saveBounds = debounce(() => {
    store.set('windowBounds', mainWindow.getBounds());
  }, 500);

  mainWindow.on('resize', saveBounds);
  mainWindow.on('move', saveBounds);
  mainWindow.on('close', saveBounds);

  app.on('will-quit', () => {
    globalShortcut.unregisterAll();
  });

  mainWindow.hide();
}


function createWindow() {

  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  const winWidth = Math.floor(width / 3);
  const winHeight = Math.floor(height / 3);

  const savedBounds = store.get('windowBounds') ||
  {
    x: width - winWidth - 10,
    y: height - winHeight - 10,
    width: winWidth,
    height: winHeight
  };

  mainWindow = new BrowserWindow({
    ...savedBounds,
    frame: false,
    alwaysOnTop: false,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.loadURL('http://localhost:3000');


  mainWindow.webContents.once('did-finish-load', () => {
    if (deepLinkUrl) {
      mainWindow.webContents.send('auth-code-received', extractCode(deepLinkUrl));
    };
  })

  return mainWindow
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.on('close-window', () => {

  if (mainWindow) mainWindow.close();
});

