const clients = require("..");

const URL = 'http://127.0.0.1:8000/api/v1';

const startServer = async (req, res) => {
    try {
        const data = await fetch(`${URL}/training/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if(!data.ok){
            res.status(500).json({ message: "Failed to start server" });
            return;
        }

        const serverData = await data.json();
        const port = serverData.fl_server_port;

        let serverStarted = false;
        let checkCount = 0;

        while(!serverStarted){
            const statusRes = await fetch(`${URL}/training/status`);
            const statusData = await statusRes.json();
            console.log("Checking server status:", statusData);

            if(statusData.total_rounds != null){
                serverStarted = true;
                res.status(200).json({ message: "Server started", status: statusData, port: port });
                return;
            }
            checkCount++;
            if(checkCount >= 30){ // timeout after 30 checks (1 minute)
                res.status(500).json({ message: "Server start timed out" });
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 2000)); // wait for 1 seconds before checking again
        }

    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const stopServer = async (req, res) => {
    try {
        const data = await fetch(`${URL}/training/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if(!data.ok){
            res.status(500).json({ message: "Failed to stop server" });
            return;
        }

        res.status(200).json({ message: "Server stopped" });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

module.exports = {
    startServer,
    stopServer
};