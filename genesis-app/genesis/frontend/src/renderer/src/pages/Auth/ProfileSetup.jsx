import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUser, FaMapMarkerAlt, FaBuilding, FaUpload, FaBrain, FaRocket, FaShieldAlt, FaCheck, FaPhone, FaPen, FaGlobe, FaLinkedin, FaTwitter, FaGithub, FaCamera, FaStar, FaAward, FaMagic } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import Lottie from 'lottie-react';
import profileAnimation from '../../assets/ProfileSetup.json';

const ProfileSetup = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    company: '',
    position: '',
    address: '',
    city: '',
    country: '',
    phone: '',
    bio: '',
    website: '',
    linkedin: '',
    twitter: '',
    github: '',
    skills: []
  });
  const [avatar, setAvatar] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeField, setActiveField] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [skillInput, setSkillInput] = useState('');
  const [particles, setParticles] = useState([]);
  const navigate = useNavigate();

  const steps = [
    { number: 1, title: 'Basic Info', icon: FaUser },
    { number: 2, title: 'Professional', icon: FaBuilding },
    { number: 3, title: 'Social', icon: FaGlobe },
    { number: 4, title: 'Bio & Skills', icon: FaPen }
  ];

  useEffect(() => {
    const initialParticles = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 1,
      duration: Math.random() * 25 + 15,
      delay: Math.random() * 5
    }));
    setParticles(initialParticles);
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatar(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        skills: [...formData.skills, skillInput.trim()]
      });
      setSkillInput('');
    }
  };

  const removeSkill = (skillToRemove) => {
    setFormData({
      ...formData,
      skills: formData.skills.filter(skill => skill !== skillToRemove)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      const userData = JSON.parse(localStorage.getItem('userData') || '{}');
      const updatedUser = {
        ...userData,
        ...formData,
        profileCompleted: true,
        avatar: avatar,
        joinedDate: new Date().toISOString(),
        profileScore: calculateProfileScore()
      };

      localStorage.setItem('userData', JSON.stringify(updatedUser));
      setIsLoading(false);
      navigate('/dashboard');
    }, 2000);
  };

  const calculateProfileScore = () => {
    let score = 0;
    const fields = ['firstName', 'lastName', 'company', 'position', 'bio'];
    fields.forEach(field => {
      if (formData[field].trim()) score += 15;
    });
    if (avatar) score += 10;
    if (formData.skills.length > 0) score += 15;
    return Math.min(score, 100);
  };

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const ProfileScore = () => {
    const score = calculateProfileScore();
    return (
      <div className="flex items-center justify-center mb-8">
        <div className="relative">
          <svg className="w-24 h-24 transform rotate-[-90deg]" viewBox="0 0 36 36">
            <path
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#E5E7EB"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845
                a 15.9155 15.9155 0 0 1 0 31.831
                a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="url(#gradient)"
              strokeWidth="3"
              strokeDasharray={`${score}, 100`}
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0098B0" />
                <stop offset="100%" stopColor="#008299" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-[#0098B0]">{score}%</span>
          </div>
        </div>
      </div>
    );
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-800">Personal Information</h3>
              <p className="text-gray-600">Let's start with the basics</p>
            </div>

            <div className="flex justify-center mb-6">
              <div className="relative group">
                <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-[#0098B0] to-[#008299] border-4 border-white shadow-2xl overflow-hidden relative">
                  {avatar ? (
                    <img src={avatar} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <FaUser className="text-5xl text-white" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center">
                    <FaCamera className="text-white text-2xl" />
                  </div>
                </div>
                <label className="absolute -bottom-2 -right-2 bg-gradient-to-r from-[#0098B0] to-[#008299] text-white p-4 rounded-xl shadow-2xl cursor-pointer hover:shadow-3xl transform hover:scale-110 transition-all duration-300 group">
                  <FaUpload className="text-lg" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                </label>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  First Name *
                </label>
                <motion.div whileFocus={{ scale: 1.02 }} className="relative">
                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleChange}
                    onFocus={() => setActiveField('firstName')}
                    onBlur={() => setActiveField(null)}
                    required
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 text-lg"
                    placeholder="John"
                  />
                </motion.div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Last Name *
                </label>
                <motion.div whileFocus={{ scale: 1.02 }} className="relative">
                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleChange}
                    onFocus={() => setActiveField('lastName')}
                    onBlur={() => setActiveField(null)}
                    required
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 text-lg"
                    placeholder="Doe"
                  />
                </motion.div>
              </div>
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-800">Professional Details</h3>
              <p className="text-gray-600">Tell us about your professional background</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FaBuilding className="mr-3 text-[#0098B0] text-lg" />
                  Company
                </label>
                <motion.div whileFocus={{ scale: 1.02 }} className="relative">
                  <input
                    type="text"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                    onFocus={() => setActiveField('company')}
                    onBlur={() => setActiveField(null)}
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 text-lg"
                    placeholder="Google Inc."
                  />
                </motion.div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Position
                </label>
                <motion.div whileFocus={{ scale: 1.02 }} className="relative">
                  <input
                    type="text"
                    name="position"
                    value={formData.position}
                    onChange={handleChange}
                    onFocus={() => setActiveField('position')}
                    onBlur={() => setActiveField(null)}
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 text-lg"
                    placeholder="Senior Developer"
                  />
                </motion.div>
              </div>
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-800">Social Profiles</h3>
              <p className="text-gray-600">Connect your social accounts</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FaGlobe className="mr-3 text-[#0098B0] text-lg" />
                  Website
                </label>
                <motion.div whileFocus={{ scale: 1.02 }} className="relative">
                  <input
                    type="url"
                    name="website"
                    value={formData.website}
                    onChange={handleChange}
                    onFocus={() => setActiveField('website')}
                    onBlur={() => setActiveField(null)}
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 text-lg"
                    placeholder="https://yourwebsite.com"
                  />
                </motion.div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <FaLinkedin className="mr-3 text-[#0077B5] text-lg" />
                    LinkedIn
                  </label>
                  <input
                    type="url"
                    name="linkedin"
                    value={formData.linkedin}
                    onChange={handleChange}
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0077B5] focus:ring-4 focus:ring-[#0077B5]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400"
                    placeholder="LinkedIn URL"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <FaTwitter className="mr-3 text-[#1DA1F2] text-lg" />
                    Twitter
                  </label>
                  <input
                    type="url"
                    name="twitter"
                    value={formData.twitter}
                    onChange={handleChange}
                    className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#1DA1F2] focus:ring-4 focus:ring-[#1DA1F2]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400"
                    placeholder="Twitter URL"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FaGithub className="mr-3 text-gray-800 text-lg" />
                  GitHub
                </label>
                <input
                  type="url"
                  name="github"
                  value={formData.github}
                  onChange={handleChange}
                  className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-gray-800 focus:ring-4 focus:ring-gray-800/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400"
                  placeholder="GitHub URL"
                />
              </div>
            </div>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-800">About & Skills</h3>
              <p className="text-gray-600">Final touches to complete your profile</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FaPen className="mr-3 text-[#0098B0] text-lg" />
                  Bio
                </label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  rows="4"
                  className="w-full px-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm placeholder-gray-400 resize-none text-lg"
                  placeholder="Tell your story... What drives you? What are your passions?"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FaAward className="mr-3 text-[#0098B0] text-lg" />
                  Skills
                </label>
                <div className="flex gap-3 mb-4">
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                    className="flex-1 px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-[#0098B0] focus:ring-4 focus:ring-[#0098B0]/20 transition-all duration-300 bg-white/80 backdrop-blur-sm"
                    placeholder="Add a skill and press Enter"
                  />
                  <button
                    type="button"
                    onClick={addSkill}
                    className="px-6 py-3 bg-gradient-to-r from-[#0098B0] to-[#008299] text-white rounded-2xl font-semibold hover:shadow-xl transform hover:scale-105 transition-all duration-300"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.skills.map((skill, index) => (
                    <motion.span
                      key={index}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0098B0] to-[#008299] text-white rounded-full text-sm font-medium"
                    >
                      <FaStar className="text-yellow-300" />
                      {skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        className="hover:text-red-200 transition-colors"
                      >
                        ×
                      </button>
                    </motion.span>
                  ))}
                </div>
              </div>

              <ProfileScore />
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-white via-blue-50 to-[#0098B0]/10 overflow-hidden relative">
      {/* Enhanced Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        {particles.map(particle => (
          <motion.div
            key={particle.id}
            className="absolute rounded-full bg-gradient-to-r from-[#0098B0]/20 to-[#008299]/15"
            style={{
              width: particle.size,
              height: particle.size,
              left: `${particle.x}%`,
              top: `${particle.y}%`,
            }}
            animate={{
              y: [0, -40, 0],
              x: [0, Math.random() * 20 - 10, 0],
              opacity: [0, 0.8, 0],
            }}
            transition={{
              duration: particle.duration,
              repeat: Infinity,
              delay: particle.delay,
              ease: "easeInOut"
            }}
          />
        ))}
        
        <motion.div
          animate={{
            y: [0, 20, 0],
            x: [0, -15, 0],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
          className="absolute bottom-40 right-16 text-5xl opacity-10"
        >
          ⭐
        </motion.div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.header 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="text-center mb-12"
        >
          <motion.div 
            className="flex items-center justify-center mb-6"
            whileHover={{ scale: 1.05 }}
          >
            <div className="bg-gradient-to-br from-[#0098B0] to-[#008299] p-4 rounded-3xl shadow-2xl relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <FaBrain className="text-4xl text-white relative z-10" />
            </div>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-5xl font-bold bg-gradient-to-r from-[#0098B0] to-[#008299] bg-clip-text text-transparent mb-4"
          >
            Create Your Profile
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-xl text-gray-600 max-w-2xl mx-auto"
          >
            Build your digital identity with Genesis. Let's craft an amazing profile together.
          </motion.p>
        </motion.header>

        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Side - Progress & Animation */}
            <motion.div 
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-1"
            >
              <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/50 p-8 h-full">
                {/* Progress Steps */}
                <div className="space-y-6 mb-8">
                  {steps.map((step, index) => {
                    const Icon = step.icon;
                    const isCompleted = currentStep > step.number;
                    const isCurrent = currentStep === step.number;
                    
                    return (
                      <motion.div
                        key={step.number}
                        className={`flex items-center space-x-4 p-4 rounded-2xl transition-all duration-300 ${
                          isCurrent 
                            ? 'bg-gradient-to-r from-[#0098B0] to-[#008299] text-white shadow-lg transform scale-105' 
                            : isCompleted
                            ? 'bg-green-50 border border-green-200'
                            : 'bg-gray-50 border border-gray-200'
                        }`}
                        whileHover={{ scale: 1.02 }}
                      >
                        <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${
                          isCurrent 
                            ? 'bg-white/20' 
                            : isCompleted
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-300 text-gray-600'
                        }`}>
                          {isCompleted ? (
                            <FaCheck className="text-lg" />
                          ) : (
                            <Icon className={`text-lg ${isCurrent ? 'text-white' : 'text-gray-600'}`} />
                          )}
                        </div>
                        <div>
                          <div className={`font-semibold ${isCurrent ? 'text-white' : 'text-gray-900'}`}>
                            {step.title}
                          </div>
                          <div className={`text-sm ${isCurrent ? 'text-white/80' : 'text-gray-500'}`}>
                            Step {step.number}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>

                {/* Animation */}
                <div className="flex justify-center">
                  <div className="w-48 h-48">
                    <Lottie 
                      animationData={profileAnimation} 
                      loop={true}
                      className="w-full h-full"
                    />
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="bg-gradient-to-br from-[#0098B0]/10 to-[#008299]/5 rounded-2xl p-6 border border-[#0098B0]/20">
                  <div className="text-center space-y-3">
                    <div className="flex items-center justify-center space-x-2 text-[#0098B0]">
                      <FaMagic />
                      <span className="font-semibold">Profile Strength</span>
                    </div>
                    <ProfileScore />
                    <p className="text-sm text-gray-600">
                      Complete all steps for a perfect profile
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Right Side - Form */}
            <motion.div 
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="lg:col-span-2"
            >
              <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/50 p-8">
                <div>
                  {renderStepContent()}

                  {/* Navigation Buttons */}
                  {currentStep < steps.length ? (
                    <div className="flex justify-between mt-12 pt-8 border-t border-gray-200">
                      <button
                        type="button"
                        onClick={prevStep}
                        disabled={currentStep === 1}
                        className={`px-8 py-4 rounded-2xl font-semibold transition-all duration-300 ${
                          currentStep === 1
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-gray-600 text-white hover:bg-gray-700 transform hover:scale-105'
                        }`}
                      >
                        Previous
                      </button>

                      <button
                        type="button"
                        onClick={nextStep}
                        className="px-8 py-4 bg-gradient-to-r from-[#0098B0] to-[#008299] text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center space-x-3"
                      >
                        <span>Next Step</span>
                        <FaRocket />
                      </button>
                    </div>
                  ) : (
                    <div className="flex justify-end mt-12 pt-8 border-t border-gray-200">
                      <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-2xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center space-x-3 disabled:opacity-50"
                      >
                        {isLoading ? (
                          <>
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Updating Profile...</span>
                          </>
                        ) : (
                          <>
                            <span>Update Profile</span>
                            <FaCheck />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileSetup;