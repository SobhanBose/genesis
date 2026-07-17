const mongoose = require("mongoose");

const activitySchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true,
  },
  description: {
    type: String,
    default: "",
    trim: true,
  },
  status: {
    type: String
  },
  time: {
    type: Date,
    default: Date.now,
  },
});

const client = new mongoose.Schema({
  userid: {
    type: String,
    required: true,
    unique: true,
  },
  name: {
    type: String,
    trim: true,
    default: "",
  },
  address: {
    type: String,
    default: "",
  },
  last_login: {
    type: Date,
    default: Date.now,
  },
  inference_count: {
    type: Number,
    default: 0,
  },
  contribution_count: {
    type: Number,
    default: 0,
  },
  total_datarows_contributed: {
    type: Number,
    default: 0,
  },
  total_datasize_contributed: {
    type: Number,
    default: 0, // in bytes
  },
  online_status: {
    type: Boolean,
    default: false,
  },
  recent_activity: {
    type: [activitySchema],
    default: [],
  },
}, { timestamps: true });


const clientSchema = mongoose.model("Client", client);
module.exports = clientSchema;