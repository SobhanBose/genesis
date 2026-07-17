const express = require('express');
const { startServer, startTraining, getClients, stopServer, stopTraining } = require('../controllers/web');


const webRouter = express.Router();

webRouter.post("/startServer", startServer);
webRouter.post("/stopServer", stopServer);

module.exports = webRouter;