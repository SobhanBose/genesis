const userSchema = require("../models/auth-schema");
const clientSchema = require("../models/client-schema");

const register = async (req, res) => {
    try {
        const { userid, password } = req.body;
        const existingUser = await userSchema.findOne({ userid });
        if (existingUser) {
            return res.status(400).json({ message: "User already exists" });
        }
        const newUser = new userSchema({ userid, password });
        await newUser.save();
        const newClient = new clientSchema({ userid });
        await newClient.save();
        res.status(201).json({ message: "User registered successfully" });
    }
    catch (error) {
        res.status(500).json({ message: error.message });
    }
}

const login = async (req, res) => {
    try {
        const { userid, password } = req.body;
        const user = await userSchema.findOne({ userid });
        if (!user) {
            return res.status(400).json({ message: "Invalid credentials" });
        }
        const isMatch = await user.comparePassword(password);
        if (!isMatch) {
            return res.status(400).json({ message: "Invalid credentials" });
        }
        res.status(200).json({ message: "Login successful" });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

module.exports = {
    register,
    login
};