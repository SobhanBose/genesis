"use strict";
const electron = require("electron");
const path = require("path");
const utils = require("@electron-toolkit/utils");
const ws = require("ws");
const Papa = require("papaparse");
const child_process = require("child_process");
const fs = require("fs");
path.join(__dirname, "../../resources/icon.png");
const listDatasets = async () => {
  const path2 = "./resources/backup";
  try {
    const files = await fs.promises.readdir(path2);
    return {
      success: true,
      fileList: files.map((file) => file.replace(".csv", ""))
    };
  } catch (err) {
    console.error("Error reading directory:", err);
    return { success: false, error: err };
  }
};
const fetchRecentDataset = async () => {
  const path2 = "./resources/dataset.csv";
  try {
    const ds = await fs.promises.readFile(path2, "utf8");
    return { success: true, data: ds };
  } catch (err) {
    console.error("Error reading recent dataset:", err);
    return { success: false, error: err };
  }
};
const fetchDatasetByName = async (name) => {
  const path2 = `./resources/backup/${name}.csv`;
  try {
    const ds = await fs.promises.readFile(path2, "utf8");
    return { success: true, data: ds };
  } catch (err) {
    console.error("Error reading dataset by name:", err);
    return { success: false, error: err };
  }
};
const overrideRecentDatasetFromRow = async (row) => {
  try {
    const path2 = "./resources/dataset.csv";
    const file = await fs.promises.readFile(path2, "utf8");
    const parsed = Papa.parse(file, { header: true, skipEmptyLines: true });
    parsed.data.push(row);
    const newDataset = Papa.unparse(parsed.data, { header: false });
    await fs.promises.writeFile(path2, newDataset);
    return { success: true };
  } catch (err) {
    console.error("Error overriding dataset:", err);
    return { success: false, error: err };
  }
};
const appendRecentDatasetFromCSV = async (parsed) => {
  try {
    const path2 = "./resources/dataset.csv";
    const newCsv = Papa.unparse(parsed.data, { header: false });
    await fs.promises.appendFile(path2, "\n" + newCsv);
    return { success: true };
  } catch (err) {
    console.error("Error overriding dataset:", err);
    return { success: false, error: err };
  }
};
const deleteDatasetByName = async (name) => {
  try {
    const path2 = `./resources/backup/${name}.csv`;
    await fs.promises.unlink(path2);
    return { success: true };
  } catch (err) {
    console.error("Error deleting file:", err);
    return { success: false, error: err };
  }
};
const changeRecentDatasetDirectoryToBackup = async () => {
  try {
    const oldPath = "./resources/dataset.csv";
    const newPath = `./resources/backup/${Date.now()}.csv`;
    await fs.promises.rename(oldPath, newPath);
    return { success: true };
  } catch (err) {
    console.error("Error moving file:", err);
    return { success: false, error: err };
  }
};
const createNewRecentDataset = async () => {
  try {
    const path2 = "./resources/dataset.csv";
    const headers = ["chr", "start", "end", "ref", "alt", "class", "gene", "phastconselements100way", "phylop100way_vertebrate", "phylop20way_mammalian", "phastcons100way_vertebrate", "phastcons20way_mammalian", "siphy_29way_logodds", "phylop30way_mammalian", "phastcons30way_mammalian", "af", "af_raw", "af_male", "af_female", "af_afr", "af_ami", "af_amr", "af_asj", "af_eas", "af_fin", "af_nfe", "af_oth", "gdi", "gdi_phred", "rvis1", "rvis2", "lof_score", "molecular_weight", "equipotential_point", "hydrophilic", "hydrophobic", "amphipathic_", "cyclic", "essential", "aromatic", "aliphatic", "nonpolar", "polar_uncharged", "acidic", "basic", "sulfur", "pka_cooh", "pka_nh3", "blosum100", "ds_ag", "ds_al", "ds_dg", "ds_dl", "dp_ag", "dp_al", "dp_dg", "dp_dl", "gm12878", "h1hesc", "hepg2", "hmec", "hsmm", "huvec", "k562", "nhek", "nhlf", "func_frameshift", "func_nonframeshift", "func_nonsynonymous_snv", "func_startloss", "func_stopgain", "func_stoploss", "omim_autosomal_dominant", "omim_autosomal_recessive", "omim_x_linked_dominant", "omim_x_linked_recessive", "omim_other"].join(",");
    await fs.promises.writeFile(path2, headers);
    return { success: true };
  } catch (err) {
    console.error("Error creating file:", err);
    return { success: false, error: err };
  }
};
const createLogFile = async (name, logsText) => {
  const path2 = "./resources/logs";
  try {
    await fs.promises.writeFile(`${path2}/${name}.log`, logsText);
    return { success: true };
  } catch (err) {
    console.error("Error creating log file:", err);
    return { success: false, error: err };
  }
};
const createMetricsFile = async (name, metricsText) => {
  const path2 = "./resources/metrics";
  try {
    await fs.promises.writeFile(`${path2}/${name}.json`, metricsText);
    return { success: true };
  } catch (err) {
    console.error("Error creating metrics file:", err);
    return { success: false, error: err };
  }
};
const fetchLogFile = async (filename) => {
  const path2 = `./resources/logs/${filename}.log`;
  try {
    const data = await fs.promises.readFile(path2, "utf8");
    return { success: true, data };
  } catch (err) {
    console.error("Error reading log file:", err);
    return { success: false, error: err };
  }
};
const fetchMetricsFile = async (filename) => {
  const path2 = `./resources/metrics/${filename}.json`;
  try {
    const data = await fs.promises.readFile(path2, "utf8");
    return { success: true, data };
  } catch (err) {
    console.error("Error reading metrics file:", err);
    return { success: false, error: err };
  }
};
const fetchMostRecentLogFile = async () => {
  const path2 = "./resources/logs";
  try {
    const files = await fs.promises.readdir(path2);
    if (files.length === 0) {
      return { success: false, error: "No log files found" };
    }
    const filesWithStats = await Promise.all(
      files.map(async (file) => {
        const stat = await fs.promises.stat(`${path2}/${file}`);
        return {
          name: file,
          time: stat.mtime.getTime()
        };
      })
    );
    const mostRecentFile = filesWithStats.sort(
      (a, b) => b.time - a.time
    )[0].name;
    const data = await fs.promises.readFile(
      `${path2}/${mostRecentFile}`,
      "utf8"
    );
    return { success: true, data };
  } catch (err) {
    console.error("Error fetching most recent log file:", err);
    return { success: false, error: err };
  }
};
const fetchMostRecentMetricsFile = async () => {
  const path2 = "./resources/metrics";
  try {
    const files = await fs.promises.readdir(path2);
    if (files.length === 0) {
      return { success: false, error: "No metrics files found" };
    }
    const filesWithStats = await Promise.all(
      files.map(async (file) => {
        const stat = await fs.promises.stat(`${path2}/${file}`);
        return {
          name: file,
          time: stat.mtime.getTime()
        };
      })
    );
    const mostRecentFile = filesWithStats.sort(
      (a, b) => b.time - a.time
    )[0].name;
    const data = await fs.promises.readFile(
      `${path2}/${mostRecentFile}`,
      "utf8"
    );
    return { success: true, data };
  } catch (err) {
    console.error("Error fetching most recent metrics file:", err);
    return { success: false, error: err };
  }
};
const listLogFiles = async () => {
  const path2 = "./resources/logs";
  try {
    const files = await fs.promises.readdir(path2);
    return { success: true, fileList: files.map((file) => file.replace(".log", "")) };
  } catch (err) {
    console.error("Error reading log directory:", err);
    return { success: false, error: err };
  }
};
const addactivity = async (userid, title, description, status) => {
  try {
    const res = await fetch(`http://localhost:3000/client/clients/add-activity/${userid}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ title, description, status })
    });
    if (!res.ok) {
      return { error: `Error: ${res.status} ${res.statusText}` };
    }
    const data = await res.json();
    console.log("Activity added:", data);
    return data;
  } catch (error) {
    return { error: error.message };
  }
};
const incrementContributionCount = async (userid) => {
  try {
    const res = await fetch(`http://localhost:3000/client/clients/increment-contribution/${userid}`, {
      method: "POST"
    });
    if (!res.ok) {
      return { error: `Error: ${res.status} ${res.statusText}` };
    }
    const data = await res.json();
    return data;
  } catch (error) {
    return { error: error.message };
  }
};
const updateTotalDataRowsAndSize = async (userid, rowsAdded, dataSize) => {
  try {
    const res = await fetch(`http://localhost:3000/client/clients/update-data-rows-and-size/${userid}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ rowsAdded, dataSize })
    });
    if (!res.ok) {
      return { error: `Error: ${res.status} ${res.statusText}` };
    }
    const data = await res.json();
    return data;
  } catch (error) {
    return { error: error.message };
  }
};
const getClientData = async (userid) => {
  try {
    const res = await fetch(`http://localhost:3000/client/clients/${userid}`);
    if (!res.ok) {
      return { error: `Error: ${res.status} ${res.statusText}` };
    }
    const data = await res.json();
    return { success: true, client: data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};
const runTraining = async (mainWindow2, port) => {
  let log = "";
  let metrics = {
    isAborted: false,
    trainingSamples: null,
    testingSamples: null,
    inputSize: null,
    rounds: []
  };
  let currentRound = null;
  let roundCounter = 0;
  const parseLine = (line) => {
    const trainMatch = line.match(/Train:\s*(\d+)/);
    if (trainMatch) metrics.trainingSamples = parseInt(trainMatch[1]);
    const testMatch = line.match(/Test:\s*(\d+)/);
    if (testMatch) metrics.testingSamples = parseInt(testMatch[1]);
    const inputSizeMatch = line.match(/'input_size':\s*(\d+)/);
    if (inputSizeMatch) metrics.inputSize = parseInt(inputSizeMatch[1]);
    if (line.includes("Received: train message")) {
      roundCounter++;
      currentRound = {
        round: roundCounter,
        status: "in-progress",
        loss: null,
        accuracy: null,
        epoch: null,
        startTime: /* @__PURE__ */ new Date(),
        endTime: null,
        timeTakenSec: null
      };
      metrics.rounds.push(currentRound);
    }
    const epochMatch = line.match(/Epoch\s+(\d+\/\d+)/);
    if (epochMatch && currentRound) {
      currentRound.epoch = epochMatch[1];
      currentRound.status = "in-progress";
    }
    const evalMatch = line.match(/Evaluation - Loss:\s*([\d.]+), Accuracy:\s*([\d.]+)/);
    if (evalMatch && currentRound) {
      currentRound.loss = parseFloat(evalMatch[1]);
      currentRound.accuracy = parseFloat(evalMatch[2]);
      currentRound.endTime = /* @__PURE__ */ new Date();
      currentRound.timeTakenSec = (currentRound.endTime - currentRound.startTime) / 1e3;
      currentRound.status = "completed";
      currentRound = null;
    }
    mainWindow2.webContents.send("training-event", {
      type: "metrics-update",
      data: metrics
    });
  };
  const projectRoot = path.join(__dirname, "../..");
  const pythonPath = path.join(
    projectRoot,
    "src/main/modelTraining/venv",
    process.platform === "win32" ? "Scripts" : "bin",
    process.platform === "win32" ? "python.exe" : "python"
  );
  const clientId = "2";
  const pyProcess2 = child_process.spawn(pythonPath, ["-u", "-m", "src.federated.client", "--client_id", clientId, "--server", `localhost:${port}`], {
    // change done
    cwd: path.join(projectRoot, "src/main/modelTraining")
    // Set cwd to project root
  });
  pyProcess2.stdout.on("data", (data) => {
    data = data.toString();
    console.log(`PYTHON: ${data}`);
    log = log + data + "\n";
    const event = {
      type: "log",
      message: data
    };
    const lines = data.split("\n");
    lines.forEach((line) => line.trim() && parseLine(line));
    mainWindow2.webContents.send("training-event", event);
  });
  pyProcess2.stderr.on("data", (data) => {
    const text = data.toString();
    log = log + text + "\n";
    if (text.includes("Traceback") || text.includes("Error")) {
      console.error(`PYTHON ERROR: ${text}`);
      const event = {
        type: "error",
        message: text
      };
      mainWindow2.webContents.send("training-event", event);
    } else {
      console.log(`PYTHON LOG: ${text}`);
      const lines = text.split("\n");
      lines.forEach((line) => line.trim() && parseLine(line));
      const event = {
        type: "log",
        message: text
      };
      mainWindow2.webContents.send("training-event", event);
    }
  });
  pyProcess2.on("close", async (code) => {
    console.log(`Python process exited with code ${code}`);
    log = log + `
Process exited with code ${code}
`;
    if (code === 0) {
      await changeRecentDatasetDirectoryToBackup();
      await createNewRecentDataset();
      await addactivity("satirtha", "Model Training Completed", "Model training completed successfully", "green");
      await incrementContributionCount("satirtha");
      await updateTotalDataRowsAndSize("satirtha", metrics.trainingSamples, metrics.trainingSamples * metrics.inputSize * 4);
    } else if (code == null) {
      await addactivity("satirtha", "Model Training stopped by Admin", "Model training process exited successfully", "red");
    } else {
      await addactivity("satirtha", "Model Training Failed", "Model training process exited with errors", "red");
    }
    const event = {
      type: "exit",
      code
    };
    mainWindow2.webContents.send("training-event", event);
    const name = `${Date.now()}`;
    await createLogFile(name, log);
    if (code !== null) {
      let event2 = { type: "training-stop" };
      mainWindow2.webContents.send("training-event", event2);
    }
    if (code === null) {
      metrics.isAborted = true;
    }
    await createMetricsFile(name, JSON.stringify(metrics, null, 2));
  });
  return pyProcess2;
};
let mainWindow;
let pyProcess;
function createWindow() {
  const iconPath = process.platform === "linux" ? path.join(__dirname, "../../resources", "GenesisLogo.png") : path.join(__dirname, "../../resources", "GenesisLogo.ico");
  const icon2 = electron.nativeImage.createFromPath(iconPath);
  mainWindow = new electron.BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    icon: icon2,
    autoHideMenuBar: true,
    ...process.platform === "linux" ? { icon: icon2 } : {},
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      sandbox: false
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    electron.shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}
function validateRow(row) {
  let errors = [];
  const requiredFields = ["chr", "start", "end", "ref", "alt", "class", "gene", "phastconselements100way", "phylop100way_vertebrate", "phylop20way_mammalian", "phastcons100way_vertebrate", "phastcons20way_mammalian", "siphy_29way_logodds", "phylop30way_mammalian", "phastcons30way_mammalian", "af", "af_raw", "af_male", "af_female", "af_afr", "af_ami", "af_amr", "af_asj", "af_eas", "af_fin", "af_nfe", "af_oth", "gdi", "gdi_phred", "rvis1", "rvis2", "lof_score", "molecular_weight", "equipotential_point", "hydrophilic", "hydrophobic", "amphipathic_", "cyclic", "essential", "aromatic", "aliphatic", "nonpolar", "polar_uncharged", "acidic", "basic", "sulfur", "pka_cooh", "pka_nh3", "blosum100", "ds_ag", "ds_al", "ds_dg", "ds_dl", "dp_ag", "dp_al", "dp_dg", "dp_dl", "gm12878", "h1hesc", "hepg2", "hmec", "hsmm", "huvec", "k562", "nhek", "nhlf", "func_frameshift", "func_nonframeshift", "func_nonsynonymous_snv", "func_startloss", "func_stopgain", "func_stoploss", "omim_autosomal_dominant", "omim_autosomal_recessive", "omim_x_linked_dominant", "omim_x_linked_recessive", "omim_other"];
  requiredFields.forEach((field) => {
    const value = row[field];
    if (!value || value.toString().trim() === "") {
      errors.push({ reason: `${field} cannot be empty` });
    }
  });
  return errors;
}
function validateDataset(parsed) {
  let errors = [];
  parsed.data.forEach((row, rowIndex) => {
    Object.keys(row).forEach((col, colIndex) => {
      const value = row[col];
      if (!value || value.trim() === "") {
        errors.push({ row: rowIndex + 2, col: colIndex + 1, reason: "Empty value" });
      }
    });
  });
  return errors;
}
electron.app.whenReady().then(() => {
  utils.electronApp.setAppUserModelId("com.electron");
  electron.app.on("browser-window-created", (_, window) => {
    utils.optimizer.watchWindowShortcuts(window);
  });
  createWindow();
  mainWindow.webContents.once("did-finish-load", () => {
    const ws$1 = new ws.WebSocket("ws://localhost:3000/ws/clinic_22");
    ws$1.on("message", async (msg) => {
      const data = JSON.parse(msg);
      if (data.type === "start_training") {
        let event = { type: "training-start" };
        mainWindow.webContents.send("training-event", event);
        pyProcess = await runTraining(mainWindow, data.port);
      } else if (data.type === "stop_training") {
        console.log("message received");
        pyProcess.kill();
      }
    });
  });
  electron.ipcMain.on("get-client-data", async (_, userid) => {
    console.log("Fetching client data for userid:", userid);
    const clientData = await getClientData(userid);
    if (!clientData.success) {
      const msg2 = { success: false, error: clientData.error };
      mainWindow.webContents.send("fetched-client-data", msg2);
      return;
    }
    const msg = {
      success: true,
      client: clientData.client
    };
    mainWindow.webContents.send("fetched-client-data", msg);
    console.log(msg);
  });
  electron.ipcMain.on("open-dataset-for-first-load", async () => {
    const dataset = await fetchRecentDataset();
    if (!dataset.success) {
      console.error("Error reading recent dataset:", dataset.error);
      return;
    }
    const msg = {
      message: "FirstLoadDataSetSend",
      dataset: dataset.data
    };
    mainWindow.webContents.send("opened-dataset-for-first-load", msg);
    console.log(msg);
  });
  electron.ipcMain.on("list-all-backup-datasets", async () => {
    const datasets = await listDatasets();
    if (!datasets.success) {
      console.error("Error listing datasets:", datasets.error);
      return;
    }
    const msg = {
      message: "ListOfAllBackupDatasets",
      datasets: datasets.fileList
    };
    mainWindow.webContents.send("listed-all-backup-datasets", msg);
    console.log(msg);
  });
  electron.ipcMain.on("open-backup-dataset-by-name", async (_, name) => {
    const dataset = await fetchDatasetByName(name);
    if (!dataset.success) {
      console.error("Error reading dataset by name:", dataset.error);
      return;
    }
    const msg = {
      message: "BackupDataSetByNameSend",
      dataset: dataset.data
    };
    mainWindow.webContents.send("opened-backup-dataset-by-name", msg);
    console.log(msg);
  });
  electron.ipcMain.on("delete-backup-dataset-by-name", async (_, name) => {
    await deleteDatasetByName(name);
    const msg = {
      message: "BackupDataSetByNameDeleted",
      name
    };
    mainWindow.webContents.send("deleted-backup-dataset-by-name", msg);
    console.log(msg);
  });
  electron.ipcMain.on("update-and-validate-csv-main", async (_, csvString) => {
    console.log("Received");
    console.log(csvString);
  });
  electron.ipcMain.on("add-row", async (_, row) => {
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
  electron.ipcMain.on("update-and-validate-csv", async (_, csvText) => {
    try {
      const parsed = Papa.parse(csvText, {
        delimiter: ",",
        header: true,
        skipEmptyLines: true
      });
      const expectedCols = 77;
      const headerCols = parsed.meta.fields || [];
      if (headerCols.length !== expectedCols) {
        const headerError = [{
          row: 0,
          col: null,
          reason: `Invalid header: expected ${expectedCols} columns but got ${headerCols.length}`
        }];
        console.log(headerError);
        mainWindow.webContents.send("csv-validation-failed", headerError);
        await addactivity("satirtha", "Dataset Validation Failed", "CSV upload failed due to header mismatch", "red");
        return;
      }
      if (parsed.errors.length > 0) {
        console.log(parsed.errors);
        console.log("Parsing Errors:", [{ row: parsed.errors[0].row + 1, col: null, reason: parsed.errors[0].message }]);
        mainWindow.webContents.send("csv-validation-failed", [{ row: parsed.errors[0].row + 1, col: null, reason: parsed.errors[0].message }]);
        await addactivity("satirtha", "Dataset Validation Failed", "CSV upload failed due to parsing errors", "red");
        return;
      }
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
  electron.ipcMain.on("get-all-logs-list", async () => {
    const logs = await listLogFiles();
    if (!logs.success) {
      console.error("Error listing logs:", logs.error);
      return;
    }
    const msg = {
      message: "ListOfAllLogs",
      logs: logs.fileList
    };
    mainWindow.webContents.send("listed-all-logs", msg);
    console.log(msg);
  });
  electron.ipcMain.on("get-most-recent-log-file", async () => {
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
    };
    const metricmsg = {
      message: "MostRecentMetricsFile",
      metrics: JSON.parse(metric.data)
    };
    mainWindow.webContents.send("fetched-most-recent-log-file", msg);
    mainWindow.webContents.send("fetched-most-recent-metrics-file", metricmsg);
    console.log(metricmsg);
  });
  electron.ipcMain.on("get-log-file-by-name", async (_, name) => {
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
    };
    const metricmsg = {
      message: "MetricsFileByName",
      metrics: JSON.parse(metric.data)
    };
    mainWindow.webContents.send("fetched-log-file-by-name", msg);
    mainWindow.webContents.send("fetched-metrics-file-by-name", metricmsg);
    console.log(metricmsg);
  });
  electron.app.on("activate", function() {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
