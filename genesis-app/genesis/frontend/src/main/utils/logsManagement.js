import { promises as fs } from 'fs';

// Create a new log file with given text
const createLogFile = async (name, logsText) => {
    const path = './resources/logs';

    try {
        await fs.writeFile(`${path}/${name}.log`, logsText);
        return { success: true };
    } catch (err) {
        console.error("Error creating log file:", err);
        return { success: false, error: err };
    }
}


// Create metrics file
const createMetricsFile = async (name, metricsText) => {
    const path = './resources/metrics';

    try {
        await fs.writeFile(`${path}/${name}.json`, metricsText);
        return { success: true };
    } catch (err) {
        console.error("Error creating metrics file:", err);
        return { success: false, error: err };
    }
}


// Fetch log file by name
const fetchLogFile = async (filename) => {
    const path = `./resources/logs/${filename}.log`;
    try {
        const data = await fs.readFile(path, 'utf8');
        return { success: true, data };
    } catch (err) {
        console.error("Error reading log file:", err);
        return { success: false, error: err };
    }
}

// Fetch metrics file by name
const fetchMetricsFile = async (filename) => {
    const path = `./resources/metrics/${filename}.json`;
    try {
        const data = await fs.readFile(path, 'utf8');
        return { success: true, data };
    } catch (err) {
        console.error("Error reading metrics file:", err);
        return { success: false, error: err };
    }
}


const fetchMostRecentLogFile = async () => {
    const path = './resources/logs';

    try {
        const files = await fs.readdir(path);

        if (files.length === 0) {
            return { success: false, error: 'No log files found' };
        }

        const filesWithStats = await Promise.all(
            files.map(async (file) => {
                const stat = await fs.stat(`${path}/${file}`);

                return {
                    name: file,
                    time: stat.mtime.getTime()
                };
            })
        );

        const mostRecentFile = filesWithStats.sort(
            (a, b) => b.time - a.time
        )[0].name;

        const data = await fs.readFile(
            `${path}/${mostRecentFile}`,
            'utf8'
        );

        return { success: true, data };

    } catch (err) {
        console.error("Error fetching most recent log file:", err);

        return { success: false, error: err };
    }
};

const fetchMostRecentMetricsFile = async () => {
    const path = './resources/metrics';

    try {
        const files = await fs.readdir(path);

        if (files.length === 0) {
            return { success: false, error: 'No metrics files found' };
        }

        const filesWithStats = await Promise.all(
            files.map(async (file) => {
                const stat = await fs.stat(`${path}/${file}`);

                return {
                    name: file,
                    time: stat.mtime.getTime()
                };
            })
        );

        const mostRecentFile = filesWithStats.sort(
            (a, b) => b.time - a.time
        )[0].name;

        const data = await fs.readFile(
            `${path}/${mostRecentFile}`,
            'utf8'
        );

        return { success: true, data };

    } catch (err) {
        console.error("Error fetching most recent metrics file:", err);

        return { success: false, error: err };
    }
};


// List all log files in logs folder
const listLogFiles = async () => {
    const path = './resources/logs';
    try {
        const files = await fs.readdir(path);
        return { success: true, fileList: files.map(file => file.replace('.log', '')) };
    } catch (err) {
        console.error("Error reading log directory:", err);
        return { success: false, error: err };
    }
}


export { createLogFile, createMetricsFile, fetchLogFile, fetchMetricsFile, fetchMostRecentLogFile, fetchMostRecentMetricsFile, listLogFiles };