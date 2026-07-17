const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const mongoose = require('mongoose');
const { WebSocketServer } = require('ws');

const clientRouter = require('./routers/client-router');
const authRouter = require('./routers/auth-router');
const webRouter = require('./routers/web-router');

require('dotenv').config();

const app = express();

app.use(bodyParser.json());
app.use(cors());


app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.use('/client', clientRouter);
app.use('/auth', authRouter);
app.use('/web', webRouter);

mongoose.connect(`mongodb+srv://ghosalsatirtha_db_user:${process.env.MONGODB}@cluster0.wubd3le.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`)
    .then(() => {
        console.log("Connected to members db")
    })
    .catch((err) => {
        console.log(err)
    })

const server = app.listen(3000, () => {
    console.log('Server is running on port 3000');
});

// --- WebSocket Server ---
const wss = new WebSocketServer({ server });
const clients = new Map(); // client_id -> websocket

wss.on('connection', (ws, req) => {
    const url = req.url; // e.g. /ws/123
    const clientId = url.split('/').pop();
    clients.set(clientId, ws);

    console.log(`Client ${clientId} connected`);

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message.toString());
            console.log(`Received from ${clientId}:`, data);
            // Handle heartbeat/updates/etc.
        } catch (err) {
            console.log('Invalid message:', message.toString());
        }
    });

    ws.on('close', () => {
        console.log(`Client ${clientId} disconnected`);
        clients.delete(clientId);
    });
});

// --- API endpoint to start a round ---
app.post('/startTraining', (req, res) => {
    const { run_id, total_rounds, port } = req.body;
    const command = {
        type: "start_training",
        run_id,
        total_rounds,
        port
    };

    for (const [cid, ws] of clients.entries()) {
        ws.send(JSON.stringify(command));
    }

    res.json({ status: "sent", run_id });
});


app.post('/stopTraining', (req, res) => {
    const command = {
        type: "stop_training"
    };
    for (const [cid, ws] of clients.entries()) {
        ws.send(JSON.stringify(command));
    }
    res.json({ status: "stop command sent" });
});

app.get('/clients', (req, res) => {
    res.json({ clients: Array.from(clients.keys()) });
});
