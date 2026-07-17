const userSchema = require("../models/auth-schema");
const clientSchema = require("../models/client-schema");

const getAllClients = async (req, res) => {
    try {
        const clients = await clientSchema.find({});
        res.status(200).json(clients);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const getClientInfo = async (req, res) => {
    try {
        const { userid } = req.params;
        const client = await clientSchema.findOne({ userid });
        if (!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        res.status(200).json(client);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const updateClientInfo = async (req, res) => {
    try {
        const { userid } = req.params;
        const updates = req.body;
        const client = await clientSchema.findOneAndUpdate({ userid }, updates, { new: true });
        if (!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        res.status(200).json(client);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const deleteClient = async (req, res) => {
    try {
        const { userid } = req.params;
        const client = await clientSchema.findOneAndDelete({ userid });
        if (!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        await userSchema.findOneAndDelete({ userid });
        
        res.status(200).json({ message: "Client deleted successfully" });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const incrementInferenceCount = async (req, res) => {
    try {
        const { userid } = req.params;
        const client = await clientSchema.findOneAndUpdate(
            { userid },
            { $inc: { inference_count: 1 } },
            { new: true }
        );
        if(!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        res.status(200).json(client);

    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const incrementContributionCount = async (req, res) => {
    try {
        const { userid } = req.params;
        const client = await clientSchema.findOneAndUpdate(
            { userid },
            { $inc: { contribution_count: 1 } },
            { new: true }
        );
        if(!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        res.status(200).json(client);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const addActivity = async (req, res) => {
    try {
        const { userid } = req.params;
        const { title, description, status } = req.body;
        const activity = { title, description, time: new Date(), status };

        const client = await clientSchema.findOneAndUpdate(
            { userid },
            { $push: { recent_activity: activity } },
            { new: true }
        );
        if (!client) {
            return res.status(404).json({ message: "Client not found" });
            console.log("Client not found");
        }
        res.status(200).json(client);
        console.log("Activity added");
    } catch (error) {
        res.status(500).json({ message: error.message });
        console.log("Error adding activity:", error.message);
    }
}

const updateTotalDataRowsAndSize = async (req, res) => {
    try {
        const { userid } = req.params;
        const { rowsAdded, dataSize } = req.body; // dataSize in bytes
        const client = await clientSchema.findOneAndUpdate(
            { userid },
            { $inc: { total_datarows_contributed: rowsAdded, total_datasize_contributed: dataSize } },
            { new: true }
        );
        if(!client) {
            return res.status(404).json({ message: "Client not found" });
        }
        res.status(200).json(client);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

module.exports = {
    getAllClients,
    getClientInfo,
    updateClientInfo,
    deleteClient,
    incrementInferenceCount,
    incrementContributionCount,
    addActivity,
    updateTotalDataRowsAndSize
};