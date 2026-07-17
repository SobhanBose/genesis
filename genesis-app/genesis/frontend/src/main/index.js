import { app, shell, BrowserWindow, ipcMain, nativeImage } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { WebSocket } from 'ws'
import icon from '../../resources/icon.png?asset'
import Papa from "papaparse"

import runTraining from './utils/runScript'
import { listDatasets, fetchRecentDataset, fetchDatasetByName, deleteDatasetByName, overrideRecentDatasetFromRow, appendRecentDatasetFromCSV } from './utils/datasetManagement'
import { fetchLogFile, fetchMetricsFile, fetchMostRecentLogFile, fetchMostRecentMetricsFile, listLogFiles } from './utils/logsManagement'
import { addactivity, getClientData } from './utils/endpointHit'

let mainWindow;
let pyProcess;

function createWindow() {

  const iconPath = process.platform === 'linux' ? join(__dirname, '../../resources', 'GenesisLogo.png') : join(__dirname, '../../resources', 'GenesisLogo.ico');
  const icon = nativeImage.createFromPath(iconPath);
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    icon: icon,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

}


function validateRow(row) {
  let errors = [];

  // Required fields
  const requiredFields = ["chr","start","end","ref","alt","class","gene","phastconselements100way","phylop100way_vertebrate","phylop20way_mammalian","phastcons100way_vertebrate","phastcons20way_mammalian","siphy_29way_logodds","phylop30way_mammalian","phastcons30way_mammalian","af","af_raw","af_male","af_female","af_afr","af_ami","af_amr","af_asj","af_eas","af_fin","af_nfe","af_oth","gdi","gdi_phred","rvis1","rvis2","lof_score","molecular_weight","equipotential_point","hydrophilic","hydrophobic","amphipathic_","cyclic","essential","aromatic","aliphatic","nonpolar","polar_uncharged","acidic","basic","sulfur","pka_cooh","pka_nh3","blosum100","ds_ag","ds_al","ds_dg","ds_dl","dp_ag","dp_al","dp_dg","dp_dl","gm12878","h1hesc","hepg2","hmec","hsmm","huvec","k562","nhek","nhlf","func_frameshift","func_nonframeshift","func_nonsynonymous_snv","func_startloss","func_stopgain","func_stoploss","omim_autosomal_dominant","omim_autosomal_recessive","omim_x_linked_dominant","omim_x_linked_recessive","omim_other"];

  requiredFields.forEach((field) => {
    const value = row[field];
    if (!value || value.toString().trim() === "") {
      errors.push({ reason: `${field} cannot be empty` });
    }
  });

  // Specific validations
  // if (row.age && isNaN(Number(row.age))) {
  //   errors.push({ reason: "Age must be a number" });
  // }

  return errors;
}


function validateDataset(parsed) {
  let errors = [];

  parsed.data.forEach((row, rowIndex) => {
    Object.keys(row).forEach((col, colIndex) => {
      const value = row[col];

      // Example validation rules:
      if (!value || value.trim() === "") {
        errors.push({ row: rowIndex + 2, col: colIndex + 1, reason: "Empty value" });
      }
    });
  });

  return errors;
}

app.whenReady().then(() => {

  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  mainWindow.webContents.once('did-finish-load', () => {
    // const ws = new WebSocket("wss://genesisbackend-trqg.onrender.com/ws/clinic_23");
    const ws = new WebSocket("ws://localhost:3000/ws/clinic_22");

    ws.on("message", async (msg) => {
      const data = JSON.parse(msg);
      if (data.type === "start_training") {

        let event = { type: "training-start" }
        mainWindow.webContents.send("training-event", event)
        
        pyProcess = await runTraining(mainWindow, data.port, pyProcess); // change port as needed
      }

      else if (data.type === "stop_training") {

        // await stopTraining(mainWindow, pyProcess);
        console.log("message received");


        pyProcess.kill();

        
      }
      
    });
  });


  // send client data on request
  ipcMain.on('get-client-data', async (_, userid) => {
    console.log("Fetching client data for userid:", userid);
    const clientData = await getClientData(userid);

    if (!clientData.success) {
      const msg = { success: false, error: clientData.error };
      mainWindow.webContents.send("fetched-client-data", msg);
      return;
    }
    const msg = {
      success: true,
      client: clientData.client
    }
    mainWindow.webContents.send("fetched-client-data", msg)
    console.log(msg);
  })


  // send dataset on first load
  ipcMain.on('open-dataset-for-first-load', async () => {
    const dataset = await fetchRecentDataset();
    if (!dataset.success) {
      console.error("Error reading recent dataset:", dataset.error);
      return;
    }
    const msg = {
      message: "FirstLoadDataSetSend",
      dataset: dataset.data
    }

    mainWindow.webContents.send("opened-dataset-for-first-load", msg)

    console.log(msg);
  })

  // send all backup datasets listed
  ipcMain.on('list-all-backup-datasets', async () => {
    const datasets = await listDatasets();
    if (!datasets.success) {
      console.error("Error listing datasets:", datasets.error);
      return;
    }
    const msg = {
      message: "ListOfAllBackupDatasets",
      datasets: datasets.fileList
    }
    mainWindow.webContents.send("listed-all-backup-datasets", msg)

    console.log(msg);
  })

  // send dataset by name
  ipcMain.on('open-backup-dataset-by-name', async (_, name) => {
    const dataset = await fetchDatasetByName(name);
    if (!dataset.success) {
      console.error("Error reading dataset by name:", dataset.error);
      return;
    }
    const msg = {
      message: "BackupDataSetByNameSend",
      dataset: dataset.data
    }
    mainWindow.webContents.send("opened-backup-dataset-by-name", msg)

    console.log(msg);
  })

  // delete dataset by name
  ipcMain.on('delete-backup-dataset-by-name', async (_, name) => {
    await deleteDatasetByName(name);

    const msg = {
      message: "BackupDataSetByNameDeleted",
      name: name
    }
    mainWindow.webContents.send("deleted-backup-dataset-by-name", msg)
    console.log(msg);
  })


  // listen for main csv validation and update
  ipcMain.on("update-and-validate-csv-main", async (_, csvString) => {
    console.log("Received");
    console.log(csvString)
  })

  // add row to recent dataset
  ipcMain.on("add-row", async (_, row) => {
    try {
      const errors = validateRow(row);

      if (errors.length > 0) {
        console.log("Row validation failed:", errors);
        mainWindow.webContents.send("add-row-failed", errors);

        await addactivity("satirtha", "Dataset Validation Failed", "Row append failed due to validation errors", "red");

        return;
      }

      const msg = await overrideRecentDatasetFromRow(row);
      if (!msg.success) {
        console.log("Row append failed in func:", msg.error);
        mainWindow.webContents.send("add-row-failed", [{ reason: "Internal error while saving row" }]);

        await addactivity("satirtha", "Dataset Update Failed", "Row append failed due to internal error", "red");
        
        return;
      }

      console.log("Row appended successfully:", row);
      mainWindow.webContents.send("add-row-success", { row });

      await addactivity("satirtha", "Dataset Updated", "Row appended successfully to dataset", "green");

    } catch (err) {
      console.error("Row append failed:", err);
      mainWindow.webContents.send("add-row-failed", [
        { reason: "Internal error while saving row" }
      ]);
      await addactivity("satirtha", "Dataset Update Failed", "Row append failed due to internal error", "red");
    }
  });

  // listen for csv validation and update
  ipcMain.on('update-and-validate-csv', async (_, csvText) => {
    try {
      const parsed = Papa.parse(csvText, {
        delimiter: ",",
        header: true,
        skipEmptyLines: true,
      });

      const expectedCols = 77;
      const headerCols = parsed.meta.fields || [];
      if (headerCols.length !== expectedCols) {
        const headerError = [{
          row: 0,
          col: null,
          reason: `Invalid header: expected ${expectedCols} columns but got ${headerCols.length}`
        }];
        console.log(headerError)
        mainWindow.webContents.send("csv-validation-failed", headerError);

        await addactivity("satirtha", "Dataset Validation Failed", "CSV upload failed due to header mismatch", "red");
        return;
      }


      if (parsed.errors.length > 0) {
        console.log(parsed.errors)
        console.log("Parsing Errors:", [{ row: parsed.errors[0].row + 1, col: null, reason: parsed.errors[0].message }]);
        mainWindow.webContents.send("csv-validation-failed", [{ row: parsed.errors[0].row + 1, col: null, reason: parsed.errors[0].message }]);

        await addactivity("satirtha", "Dataset Validation Failed", "CSV upload failed due to parsing errors", "red");
        return;
      }

      // Run custom validation
      const validationErrors = validateDataset(parsed);

      if (validationErrors.length > 0) {
        console.log("Validation failed:", validationErrors);
        mainWindow.webContents.send("csv-validation-failed", validationErrors);

        await addactivity("satirtha", "Dataset Validation Failed", "CSV upload failed due to validation errors", "red");
        return;

      } else {
        console.log("Validation success, appending...");

        const msg = await appendRecentDatasetFromCSV(parsed);
        if (!msg.success) {
          console.log("Append failed in func:", msg.error);
          mainWindow.webContents.send("csv-parsing-failed", { error: "Internal error while saving CSV" });
          
          await addactivity("satirtha", "Dataset Update Failed", "CSV upload failed due to internal error", "red");
          
          return;
        }

        mainWindow.webContents.send("csv-validation-success", {
          message: "Dataset appended successfully",
          addedRows: parsed.data.length
        });

        await addactivity("satirtha", "Dataset Updated", "CSV uploaded and dataset updated successfully", "green");
      }
    } catch (err) {
      console.error("Validation Exception:", { error: err });
      mainWindow.webContents.send("csv-parsing-failed", { error: err });
      await addactivity("satirtha", "Dataset Update Failed", "CSV upload failed due to internal error", "red");
    }
  });

  // get all logs list
  ipcMain.on('get-all-logs-list', async () => {
    const logs = await listLogFiles();
    if (!logs.success) {
      console.error("Error listing logs:", logs.error);
      return;
    }
    const msg = {
      message: "ListOfAllLogs",
      logs: logs.fileList
    }
    mainWindow.webContents.send("listed-all-logs", msg)
    console.log(msg);
  })

  // get most recent log file
  ipcMain.on('get-most-recent-log-file', async () => {
    const log = await fetchMostRecentLogFile();
    const metric = await fetchMostRecentMetricsFile();

    if (!metric.success) {
      console.error("Error fetching most recent metrics file:", metric.error);
      return;
    }
    if (!log.success) {
      console.error("Error fetching most recent log file:", log.error);
      return;
    }

    const msg = {
      message: "MostRecentLogFile",
      log: log.data
    }
    const metricmsg = {
      message: "MostRecentMetricsFile",
      metrics: JSON.parse(metric.data)
    }

    mainWindow.webContents.send("fetched-most-recent-log-file", msg)
    mainWindow.webContents.send("fetched-most-recent-metrics-file", metricmsg);

    console.log(metricmsg);
  })

  // get log file by name
  ipcMain.on('get-log-file-by-name', async (_, name) => {
    const log = await fetchLogFile(name);
    const metric = await fetchMetricsFile(name);

    if (!metric.success) {
      console.error("Error fetching metrics file by name:", metric.error);
      return;
    }
    if (!log.success) {
      console.error("Error fetching log file by name:", log.error);
      return;
    }

    
    const msg = {
      message: "LogFileByName",
      log: log.data
    }
    const metricmsg = {
      message: "MetricsFileByName",
      metrics: JSON.parse(metric.data)
    }

    mainWindow.webContents.send("fetched-log-file-by-name", msg);
    mainWindow.webContents.send("fetched-metrics-file-by-name", metricmsg);

    console.log(metricmsg);
  })


  app.on('activate', function () {

    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })

})


app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
