import { spawn } from "child_process";
import path from "path";
import { changeRecentDatasetDirectoryToBackup, createNewRecentDataset } from "./datasetManagement";
import { createLogFile, createMetricsFile } from "./logsManagement";
import { addactivity, incrementContributionCount, updateTotalDataRowsAndSize } from "./endpointHit";

const runTraining = async (mainWindow, port) => {

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

    // function to parse metrics from log lines
    const parseLine = (line) => {
        // 1️⃣ Extract static info
        const trainMatch = line.match(/Train:\s*(\d+)/);
        if (trainMatch) metrics.trainingSamples = parseInt(trainMatch[1]);

        const testMatch = line.match(/Test:\s*(\d+)/);
        if (testMatch) metrics.testingSamples = parseInt(testMatch[1]);

        const inputSizeMatch = line.match(/'input_size':\s*(\d+)/);
        if (inputSizeMatch) metrics.inputSize = parseInt(inputSizeMatch[1]);

        // 2️⃣ Detect round start
        if (line.includes("Received: train message")) {
            roundCounter++;
            currentRound = {
                round: roundCounter,
                status: "in-progress",
                loss: null,
                accuracy: null,
                epoch: null,
                startTime: new Date(),
                endTime: null,
                timeTakenSec: null
            };
            metrics.rounds.push(currentRound);
        }

        // 3️⃣ Detect epoch update
        const epochMatch = line.match(/Epoch\s+(\d+\/\d+)/);
        if (epochMatch && currentRound) {
            currentRound.epoch = epochMatch[1];
            currentRound.status = "in-progress";
        }

        // 4️⃣ Detect evaluation (end of round)
        const evalMatch = line.match(/Evaluation - Loss:\s*([\d.]+), Accuracy:\s*([\d.]+)/);
        if (evalMatch && currentRound) {
            currentRound.loss = parseFloat(evalMatch[1]);
            currentRound.accuracy = parseFloat(evalMatch[2]);
            currentRound.endTime = new Date();
            currentRound.timeTakenSec = (currentRound.endTime - currentRound.startTime) / 1000;
            currentRound.status = "completed";
            currentRound = null;
        }



        // Send metrics to frontend
        mainWindow.webContents.send("training-event", {
            type: "metrics-update",
            data: metrics
        });
    };

    // Path to Python inside your venv
    const projectRoot = path.join(__dirname, "../..");

    const pythonPath = path.join(
        projectRoot,
        "src/main/modelTraining/venv",
        process.platform === "win32" ? "Scripts" : "bin",
        process.platform === "win32" ? "python.exe" : "python"
    );

    // Example argument
    const clientId = "2";

    // Spawn the Python process
    const pyProcess = spawn(pythonPath, ["-u", "-m", "src.federated.client", "--client_id", clientId, "--server", `localhost:${port}`], { // change done
        cwd: path.join(projectRoot, "src/main/modelTraining"), // Set cwd to project root
    });

    // Capture stdout
    pyProcess.stdout.on("data", (data) => {
        data = data.toString();

        console.log(`PYTHON: ${data}`);

        log = log + data + "\n";
        const event = {
            type: "log",
            message: data
        }

        const lines = data.split("\n");
        lines.forEach((line) => line.trim() && parseLine(line));

        mainWindow.webContents.send("training-event", event)

    });

    pyProcess.stderr.on("data", (data) => {
        const text = data.toString();

        log = log + text + "\n";

        if (text.includes("Traceback") || text.includes("Error")) {
            console.error(`PYTHON ERROR: ${text}`);

            const event = {
                type: "error",
                message: text
            }

            mainWindow.webContents.send("training-event", event)

        } else {
            console.log(`PYTHON LOG: ${text}`);

            const lines = text.split("\n");
            lines.forEach((line) => line.trim() && parseLine(line));

            const event = {
                type: "log",
                message: text
            }
            mainWindow.webContents.send("training-event", event)
        }
    });

    // Capture exit
    pyProcess.on("close", async (code) => {
        console.log(`Python process exited with code ${code}`);

        log = log + `\nProcess exited with code ${code}\n`;

        // if exit code is 0, then training was successful
        // so we can move the recent dataset to backup and create a new recent dataset

        if (code === 0) {
            await changeRecentDatasetDirectoryToBackup();
            await createNewRecentDataset();

            await addactivity("satirtha", "Model Training Completed", "Model training completed successfully", "green");
            await incrementContributionCount("satirtha");
            await updateTotalDataRowsAndSize("satirtha", metrics.trainingSamples, metrics.trainingSamples * metrics.inputSize * 4); // assuming float32 (4 bytes)
        }
        else if(code == null){
            await addactivity("satirtha", "Model Training stopped by Admin", "Model training process exited successfully", "red");
        }
        else{
            await addactivity("satirtha", "Model Training Failed", "Model training process exited with errors", "red");

        }

        const event = {
            type: "exit",
            code: code
        }
        mainWindow.webContents.send("training-event", event)

        // save log file
        const name = `${Date.now()}`;
        await createLogFile(name, log);
        if(code!==null){
            let event = { type: "training-stop" }
            mainWindow.webContents.send("training-event", event)
        }
        if(code === null){
            metrics.isAborted = true;
        }
        
        await createMetricsFile(name, JSON.stringify(metrics, null, 2));
        
    });

    return pyProcess;
}

export default runTraining;