const express = require('express');
const { getAllClients, getClientInfo, updateClientInfo, deleteClient, incrementInferenceCount, incrementContributionCount, addActivity, updateTotalDataRowsAndSize } = require('../controllers/client');

const clientRouter = express.Router();

clientRouter.get('/clients', getAllClients);
clientRouter.get('/clients/:userid', getClientInfo);
clientRouter.put('/clients/:userid', updateClientInfo);
clientRouter.delete('/clients/:userid', deleteClient);
clientRouter.post('/clients/increment-inference/:userid', incrementInferenceCount);
clientRouter.post('/clients/increment-contribution/:userid', incrementContributionCount);
clientRouter.post('/clients/add-activity/:userid', addActivity);
clientRouter.post('/clients/update-data-rows-and-size/:userid', updateTotalDataRowsAndSize);

module.exports = clientRouter;