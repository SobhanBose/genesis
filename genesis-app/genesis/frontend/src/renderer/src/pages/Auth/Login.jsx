import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { FaEye, FaEyeSlash, FaBrain, FaGoogle, FaGithub, FaShieldAlt, FaRocket, FaWaveSquare } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import Lottie from 'lottie-react';
import loginAnimation from '../../assets/LoginAndSignUp.json';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [isHovered, setIsHovered] = useState(false);
  const [activeField, setActiveField] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Particle background effect
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    
    if (token && userData) {
      const user = JSON.parse(userData);
      if (user.profileCompleted) {
        navigate('/dashboard');
      } else {
        navigate('/profile-setup');
      }
    }

    // Initialize particles
    const initialParticles = Array.from({ length: 15 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 20 + 10,
      delay: Math.random() * 5
    }));
    setParticles(initialParticles);
  }, [navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);

    try {
      setTimeout(() => {
        const mockUser = {
          email: formData.email,
          name: formData.email.split('@')[0],
          profileCompleted: false,
          avatar: null
        };

        localStorage.setItem('authToken', 'mock-jwt-token-' + Date.now());
        localStorage.setItem('userData', JSON.stringify(mockUser));
        
        setIsLoading(false);
        
        const from = location.state?.from?.pathname || '/profile-setup';
        navigate(from, { replace: true });
      }, 1500);
    } catch (error) {
      setIsLoading(false);
      setErrors({ submit: 'Login failed. Please try again.' });
    }
  };

  const handleDemoLogin = () => {
    setFormData({
      email: 'demo@genesis.com',
      password: 'demo123'
    });
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-white via-blue-50 to-[#0098B0]/10 overflow-hidden relative">
      {/* Animated Background Particles */}
      <div className="absolute inset-0 overflow-hidden">
        {particles.map(particle => (
          <motion.div
            key={particle.id}
            className="absolute rounded-full bg-gradient-to-r from-[#0098B0]/20 to-[#008299]/10"
            style={{
              width: particle.size,
              height: particle.size,
              left: `${particle.x}%`,
              top: `${particle.y}%`,
            }}
            animate={{
              y: [0, -30, 0],
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
        
        {/* Animated Waves */}
        <div className="absolute bottom-0 left-0 right-0">
          <motion.div
            className="h-20 bg-gradient-to-r from-[#0098B0]/10 to-[#008299]/5"
            animate={{
              clipPath: [
                "polygon(0 45%, 100% 65%, 100% 100%, 0% 100%)",
                "polygon(0 65%, 100% 45%, 100% 100%, 0% 100%)",
                "polygon(0 45%, 100% 65%, 100% 100%, 0% 100%)"
              ]
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </div>
      </div>

      {/* Header */}
      <motion.header 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="w-full py-6 lg:py-8 flex-shrink-0 relative z-10"
      >
        <div className="max-w-7xl mx-auto px-4 text-center">
          <motion.div 
            className="flex items-center justify-center mb-3"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="bg-gradient-to-br from-[#0098B0] to-[#008299] p-3 rounded-2xl shadow-lg relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <FaBrain className="text-3xl text-white relative z-10" />
            </div>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#0098B0] to-[#008299] bg-clip-text text-transparent mb-2"
          >
            Welcome Back
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-gray-600 text-base lg:text-lg"
          >
            Continue your journey with Genesis
          </motion.p>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 py-4 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center justify-center h-full mb-10">
          
          {/* Left Side - Enhanced Animation */}
          <motion.div 
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="flex items-center justify-center h-full"
          >
            <div className="w-full max-w-lg lg:max-w-2xl relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-[#0098B0]/10 to-[#008299]/5 rounded-3xl blur-xl"></div>
              <Lottie 
                animationData={loginAnimation} 
                loop={true}
                className="w-full h-auto relative z-10"
              />
              
              {/* Floating Elements */}
              <motion.div
                animate={{
                  y: [0, -20, 0],
                  rotate: [0, 5, 0],
                }}
                transition={{
                  duration: 6,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="absolute top-10 left-10 bg-white/80 backdrop-blur-sm p-3 rounded-2xl shadow-lg border border-[#0098B0]/20"
              >
                <FaRocket className="text-[#0098B0] text-xl" />
              </motion.div>
              
              <motion.div
                animate={{
                  y: [0, 15, 0],
                  rotate: [0, -3, 0],
                }}
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 1
                }}
                className="absolute bottom-10 right-10 bg-white/80 backdrop-blur-sm p-3 rounded-2xl shadow-lg border border-[#008299]/20"
              >
                <FaWaveSquare className="text-[#008299] text-xl" />
              </motion.div>
            </div>
          </motion.div>

          {/* Right Side - Enhanced Login Form */}
          <motion.div 
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.6 }}
            className="flex items-center justify-center h-full"
          >
            <div className="w-full max-w-md">
              <div className="relative">
                {/* Glass morphism effect */}
                <div className="absolute -inset-4 bg-gradient-to-r from-[#0098B0]/5 to-[#008299]/10 rounded-3xl blur-xl opacity-75"></div>
                
                <div className="relative bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-2xl overflow-hidden">
                  {/* Header Accent */}
                  <div className="h-2 bg-gradient-to-r from-[#0098B0] to-[#008299]"></div>
                  
                  <div className="p-6 lg:p-8">
                    <motion.form 
                      onSubmit={handleSubmit} 
                      className="space-y-6"
                      initial="initial"
                      animate="animate"
                    >
                      {/* Email Field */}
                      <motion.div variants={{ initial: { opacity: 0 }, animate: { opacity: 1 } }}>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Email Address
                        </label>
                        <motion.div
                          whileFocus={{ scale: 1.02 }}
                          className="relative"
                        >
                          <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            onFocus={() => setActiveField('email')}
                            onBlur={() => setActiveField(null)}
                            required
                            className={`w-full px-4 py-3 rounded-xl border-2 transition-all duration-300 bg-white/90 backdrop-blur-sm placeholder-gray-400
                              ${errors.email ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200' : 
                                activeField === 'email' ? 'border-[#0098B0] ring-4 ring-[#0098B0]/10' : 'border-gray-200/80 focus:border-[#0098B0] focus:ring-2 focus:ring-[#0098B0]/10'}`}
                            placeholder="Enter your email"
                          />
                          <AnimatePresence>
                            {activeField === 'email' && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0 }}
                                className="absolute -top-2 left-3 bg-white px-1 text-xs text-[#0098B0] font-semibold"
                              >
                                Email
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </motion.div>
                        {errors.email && (
                          <motion.p 
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-red-500 text-sm mt-1 flex items-center"
                          >
                            • {errors.email}
                          </motion.p>
                        )}
                      </motion.div>

                      {/* Password Field */}
                      <motion.div variants={{ initial: { opacity: 0 }, animate: { opacity: 1 } }}>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Password
                        </label>
                        <motion.div
                          whileFocus={{ scale: 1.02 }}
                          className="relative"
                        >
                          <input
                            type={showPassword ? 'text' : 'password'}
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            onFocus={() => setActiveField('password')}
                            onBlur={() => setActiveField(null)}
                            required
                            className={`w-full px-4 py-3 rounded-xl border-2 transition-all duration-300 bg-white/90 backdrop-blur-sm placeholder-gray-400 pr-12
                              ${errors.password ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200' : 
                                activeField === 'password' ? 'border-[#0098B0] ring-4 ring-[#0098B0]/10' : 'border-gray-200/80 focus:border-[#0098B0] focus:ring-2 focus:ring-[#0098B0]/10'}`}
                            placeholder="Enter your password"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-[#0098B0] transition-colors p-1 rounded-lg hover:bg-[#0098B0]/10"
                          >
                            {showPassword ? <FaEyeSlash size={18} /> : <FaEye size={18} />}
                          </button>
                          <AnimatePresence>
                            {activeField === 'password' && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0 }}
                                className="absolute -top-2 left-3 bg-white px-1 text-xs text-[#0098B0] font-semibold"
                              >
                                Password
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </motion.div>
                        {errors.password && (
                          <motion.p 
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-red-500 text-sm mt-1 flex items-center"
                          >
                            • {errors.password}
                          </motion.p>
                        )}
                      </motion.div>

                      {/* Error Message */}
                      <AnimatePresence>
                        {errors.submit && (
                          <motion.div 
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="bg-red-50 border border-red-200 rounded-xl p-3"
                          >
                            <p className="text-red-600 text-sm">{errors.submit}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Remember Me & Forgot Password */}
                      <div className="flex items-center justify-between">
                        <label className="flex items-center space-x-2 cursor-pointer group">
                          <div className="relative">
                            <input
                              type="checkbox"
                              className="sr-only"
                            />
                            <div className="w-5 h-5 rounded border-2 border-gray-300 group-hover:border-[#0098B0] transition-colors flex items-center justify-center">
                              <motion.div
                                initial={{ scale: 0 }}
                                whileTap={{ scale: 0.8 }}
                                className="w-3 h-3 bg-[#0098B0] rounded-sm"
                              />
                            </div>
                          </div>
                          <span className="text-sm text-gray-600 font-medium group-hover:text-gray-700 transition-colors">
                            Remember me
                          </span>
                        </label>
                        <motion.a 
                          href="#" 
                          className="text-sm font-semibold text-[#0098B0] hover:text-[#008299] transition-colors relative group"
                          whileHover={{ x: 2 }}
                        >
                          Forgot password?
                          <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-[#0098B0] group-hover:w-full transition-all duration-300"></span>
                        </motion.a>
                      </div>

                      {/* Sign In Button */}
                      <motion.button
                        type="submit"
                        disabled={isLoading}
                        onHoverStart={() => setIsHovered(true)}
                        onHoverEnd={() => setIsHovered(false)}
                        className="w-full bg-gradient-to-r from-[#0098B0] to-[#008299] text-white py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl relative overflow-hidden group"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                        
                        {isLoading ? (
                          <div className="flex items-center justify-center space-x-2 relative z-10">
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                              className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                            ></motion.div>
                            <span>Signing in...</span>
                          </div>
                        ) : (
                          <span className="relative z-10">Sign In</span>
                        )}
                      </motion.button>
                    </motion.form>


                    {/* Divider */}
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.8 }}
                      className="my-6 flex items-center"
                    >
                      <div className="flex-1 border-t border-gray-200/60"></div>
                      <span className="px-3 text-sm text-gray-500 font-medium bg-white/50 rounded-lg">or continue with</span>
                      <div className="flex-1 border-t border-gray-200/60"></div>
                    </motion.div>

                    {/* Social Login */}
                    <div className="grid grid-cols-2 gap-3">
                      <motion.button 
                        className="flex items-center justify-center p-3 rounded-xl border border-gray-200/80 hover:border-gray-300 hover:bg-white/80 transition-all duration-300 bg-white/50 backdrop-blur-sm group relative overflow-hidden"
                        whileHover={{ y: -2 }}
                        whileTap={{ y: 0 }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-red-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <FaGoogle className="text-red-500 mr-2 group-hover:scale-110 transition-transform duration-300 relative z-10" />
                        <span className="text-sm font-medium text-gray-700 relative z-10">Google</span>
                      </motion.button>
                      <motion.button 
                        className="flex items-center justify-center p-3 rounded-xl border border-gray-200/80 hover:border-gray-300 hover:bg-white/80 transition-all duration-300 bg-white/50 backdrop-blur-sm group relative overflow-hidden"
                        whileHover={{ y: -2 }}
                        whileTap={{ y: 0 }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-gray-800/5 to-gray-900/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <FaGithub className="text-gray-800 mr-2 group-hover:scale-110 transition-transform duration-300 relative z-10" />
                        <span className="text-sm font-medium text-gray-700 relative z-10">GitHub</span>
                      </motion.button>
                    </div>

                    {/* Sign up link */}
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1.1 }}
                      className="text-center mt-6 pt-6 border-t border-gray-200/30"
                    >
                      <p className="text-gray-600 text-sm">
                        Don't have an account?{' '}
                        <Link 
                          to="/signup" 
                          className="font-semibold text-[#0098B0] hover:text-[#008299] transition-colors relative group"
                        >
                          Create one now
                          <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-[#0098B0] group-hover:w-full transition-all duration-300"></span>
                        </Link>
                      </p>
                    </motion.div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Login;