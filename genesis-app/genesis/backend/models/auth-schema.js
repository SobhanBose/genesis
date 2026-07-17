const bcrypt = require("bcrypt");
const mongoose = require("mongoose");

const SALT_ROUNDS = 10; // you can increase if needed

const user = new mongoose.Schema({
  userid: {
    type: String,
    required: true,
    unique: true,
    trim: true,
  },
  password: {
    type: String,
    required: true,
  }
}, { timestamps: true });

// Hash password before saving
user.pre("save", async function (next) {
  if (!this.isModified("password")) return next();

  try {
    const salt = await bcrypt.genSalt(SALT_ROUNDS);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

// Method to compare passwords
user.methods.comparePassword = async function (candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password);
};

const userSchema = mongoose.model("User", user);

module.exports = userSchema;
