import React, { useState } from 'react';
import { 
  Activity, 
  Eye, 
  EyeOff, 
  LogIn, 
  UserPlus, 
  Shield, 
  Stethoscope, 
  UserCheck, 
  Heart, 
  User, 
  CheckCircle2, 
  Sparkles,
  Phone,
  Building2,
  Award
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function LoginPage({ onLogin }) {
  const { login, register, quickLogin } = useAuth();
  const [activeTab, setActiveTab] = useState('login'); // 'login' | 'register'

  // Sign In Form State
  const [loginForm, setLoginForm] = useState({ username_or_email: '', password: '' });
  const [showLoginPass, setShowLoginPass] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);

  // Register Form State
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    full_name: '',
    role: 'PATIENT',
    // Role-specific fields
    age: '35',
    gender: 'Male',
    phone: '',
    department: 'General Medicine',
    blood_group: 'O+',
    specialization: 'General Medicine',
    experience_years: '5'
  });
  const [showRegisterPass, setShowRegisterPass] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);

  // Common UI State
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [quickLoading, setQuickLoading] = useState(null);

  const departments = [
    'General Medicine',
    'Cardiology',
    'Neurology',
    'Orthopedics',
    'Pediatrics',
    'Dermatology',
    'Emergency Medicine'
  ];

  const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

  // Handle Login Submit
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!loginForm.username_or_email || !loginForm.password) {
      setError('Please provide your username/email and password.');
      return;
    }
    setLoginLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      await login(loginForm.username_or_email.trim(), loginForm.password);
      if (onLogin) onLogin();
    } catch (err) {
      setError(err.message || 'Invalid username/email or password. Please try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  // Handle Register Submit
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    // Validations
    if (!registerForm.full_name.trim()) {
      setError('Full Name is required.');
      return;
    }
    if (!registerForm.username.trim() || registerForm.username.length < 3) {
      setError('Username must be at least 3 characters.');
      return;
    }
    if (!registerForm.email.trim() || !registerForm.email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!registerForm.password || registerForm.password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (registerForm.password !== registerForm.confirm_password) {
      setError('Passwords do not match.');
      return;
    }

    setRegisterLoading(true);
    try {
      const payload = {
        username: registerForm.username.trim(),
        email: registerForm.email.trim(),
        password: registerForm.password,
        full_name: registerForm.full_name.trim(),
        role: registerForm.role,
        department: registerForm.department,
      };

      if (registerForm.role === 'PATIENT') {
        payload.age = parseInt(registerForm.age, 10) || 30;
        payload.gender = registerForm.gender;
        payload.phone = registerForm.phone.trim() || '9876543200';
        payload.blood_group = registerForm.blood_group;
      } else if (registerForm.role === 'DOCTOR') {
        payload.specialization = registerForm.specialization.trim() || registerForm.department;
        payload.experience_years = parseInt(registerForm.experience_years, 10) || 5;
      }

      await register(payload);
      setSuccessMsg(`Welcome, ${payload.full_name}! Account created and signed in.`);
      setTimeout(() => {
        if (onLogin) onLogin();
      }, 500);
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your details and try again.');
    } finally {
      setRegisterLoading(false);
    }
  };

  // Quick Demo Login
  const handleQuickLogin = async (role) => {
    setQuickLoading(role);
    setError('');
    setSuccessMsg('');
    try {
      await quickLogin(role);
      if (onLogin) onLogin();
    } catch (err) {
      setError(err.message || `Quick login failed for ${role}`);
    } finally {
      setQuickLoading(null);
    }
  };

  const quickRoles = [
    { key: 'admin', label: 'Admin', email: 'admin@carecoord.demo', roleName: 'Hospital Administrator', Icon: Shield, color: 'border-cyan-500/40 hover:bg-cyan-500/10 text-cyan-400' },
    { key: 'receptionist', label: 'Receptionist', email: 'reception@carecoord.demo', roleName: 'Front Desk Desk', Icon: UserCheck, color: 'border-purple-500/40 hover:bg-purple-500/10 text-purple-400' },
    { key: 'doctor', label: 'Doctor', email: 'doctor@carecoord.demo', roleName: 'Dr. Mehta (Cardiology)', Icon: Stethoscope, color: 'border-emerald-500/40 hover:bg-emerald-500/10 text-emerald-400' },
    { key: 'nurse', label: 'Nurse', email: 'nurse@carecoord.demo', roleName: 'Ward & ICU Triage', Icon: Heart, color: 'border-amber-500/40 hover:bg-amber-500/10 text-amber-400' },
    { key: 'patient', label: 'Patient', email: 'patient@carecoord.demo', roleName: 'Rahul Sharma (P001)', Icon: User, color: 'border-blue-500/40 hover:bg-blue-500/10 text-blue-400' },
  ];

  return (
    <div className="min-h-screen bg-dark-900 flex flex-col justify-center items-center px-4 py-8 select-none">
      {/* Brand Header */}
      <div className="mb-6 flex flex-col items-center text-center">
        <div className="p-3 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-2xl shadow-xl shadow-cyan-500/20 text-white mb-3 flex items-center justify-center">
          <Activity className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          CareCoord <span className="text-cyan-400 font-mono text-xs px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60">AI HOSPITAL OPS</span>
        </h1>
        <p className="text-xs text-gray-400 font-mono mt-1">Multi-Agent Hospital Operations & Resource Optimization</p>
        <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          ACTIVE HOSPITAL WORKFLOW SYSTEM
        </div>
      </div>

      {/* Main Container Card */}
      <div className="w-full max-w-lg bg-dark-800 border border-dark-700/80 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-sm">
        
        {/* Navigation Tabs: Sign In / Create Account */}
        <div className="grid grid-cols-2 p-1 bg-dark-900 border border-dark-700 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => { setActiveTab('login'); setError(''); setSuccessMsg(''); }}
            className={`flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'login'
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-600/20'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('register'); setError(''); setSuccessMsg(''); }}
            className={`flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'register'
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-600/20'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Account</span>
          </button>
        </div>

        {/* Global Error & Success Banners */}
        {error && (
          <div className="mb-5 p-3.5 bg-red-950/60 border border-red-800/80 text-red-300 text-xs rounded-xl flex items-start gap-2.5">
            <span className="text-red-400 font-bold shrink-0">⚠</span>
            <div className="flex-1 leading-relaxed">{error}</div>
          </div>
        )}

        {successMsg && (
          <div className="mb-5 p-3.5 bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs rounded-xl flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>{successMsg}</div>
          </div>
        )}

        {/* TAB 1: SIGN IN FORM */}
        {activeTab === 'login' && (
          <div>
            <div className="mb-4">
              <h2 className="text-base font-semibold text-white">Sign In to Your Account</h2>
              <p className="text-xs text-gray-400">Enter your credentials or choose a quick demo persona below.</p>
            </div>

            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Email or Username
                </label>
                <input
                  type="text"
                  value={loginForm.username_or_email}
                  onChange={(e) => setLoginForm({ ...loginForm, username_or_email: e.target.value })}
                  placeholder="e.g. admin@carecoord.demo or admin"
                  className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-600 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                  autoComplete="username"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-medium text-gray-300">
                    Password
                  </label>
                  <span className="text-[10px] text-gray-500 font-mono">Demo: Demo@1234</span>
                </div>
                <div className="relative">
                  <input
                    type={showLoginPass ? 'text' : 'password'}
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    placeholder="Enter your password"
                    className="w-full px-3.5 py-2.5 pr-10 bg-dark-900 border border-dark-600 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPass(!showLoginPass)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-200 transition-colors"
                  >
                    {showLoginPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs rounded-xl transition-all shadow-md shadow-cyan-600/20 disabled:opacity-60 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loginLoading ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    <span>Sign In to Hospital Portal</span>
                  </>
                )}
              </button>
            </form>

            {/* 1-Click Quick Demo Sign-in */}
            <div className="mt-6 pt-5 border-t border-dark-700">
              <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider font-mono mb-3 text-center flex items-center justify-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>1-Click Evaluator Demo Sign-In</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {quickRoles.map((r) => {
                  const Icon = r.Icon;
                  const isSpinning = quickLoading === r.key;
                  return (
                    <button
                      key={r.key}
                      type="button"
                      disabled={!!quickLoading}
                      onClick={() => handleQuickLogin(r.key)}
                      className={`flex items-center gap-2.5 p-2.5 rounded-xl border text-left transition-all text-xs ${r.color} disabled:opacity-50 cursor-pointer`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-white leading-tight flex items-center justify-between">
                          <span>{r.label}</span>
                          {isSpinning && <span className="w-3 h-3 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></span>}
                        </div>
                        <div className="text-[10px] text-gray-400 truncate">{r.roleName}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: REGISTER / CREATE ACCOUNT FORM */}
        {activeTab === 'register' && (
          <div>
            <div className="mb-4">
              <h2 className="text-base font-semibold text-white">Create New User Account</h2>
              <p className="text-xs text-gray-400">Register as a patient, doctor, nurse, or receptionist.</p>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
              
              {/* Role Selection */}
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Select Role
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                  {[
                    { id: 'PATIENT', label: 'Patient', icon: User },
                    { id: 'DOCTOR', label: 'Doctor', icon: Stethoscope },
                    { id: 'NURSE', label: 'Nurse', icon: Heart },
                    { id: 'RECEPTIONIST', label: 'Reception', icon: UserCheck },
                  ].map((r) => {
                    const RoleIcon = r.icon;
                    const isSelected = registerForm.role === r.id;
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => setRegisterForm({ ...registerForm, role: r.id })}
                        className={`flex flex-col items-center justify-center p-2 rounded-xl border text-xs transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-cyan-500/10 border-cyan-500 text-cyan-400 font-semibold shadow-sm'
                            : 'bg-dark-900 border-dark-600 text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        <RoleIcon className="w-4 h-4 mb-1" />
                        <span className="text-[11px]">{r.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Full Name & Username */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={registerForm.full_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })}
                    placeholder="e.g. Ramesh Chandra"
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Username *
                  </label>
                  <input
                    type="text"
                    required
                    value={registerForm.username}
                    onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                    placeholder="e.g. ramesh_c"
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                  placeholder="e.g. ramesh@example.com"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              {/* Password & Confirm */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Password *
                  </label>
                  <div className="relative">
                    <input
                      type={showRegisterPass ? 'text' : 'password'}
                      required
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      placeholder="Min 6 characters"
                      className="w-full px-3 py-2 pr-8 bg-dark-900 border border-dark-600 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegisterPass(!showRegisterPass)}
                      className="absolute right-2.5 top-2 text-gray-400 hover:text-gray-200"
                    >
                      {showRegisterPass ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Confirm Password *
                  </label>
                  <input
                    type="password"
                    required
                    value={registerForm.confirm_password}
                    onChange={(e) => setRegisterForm({ ...registerForm, confirm_password: e.target.value })}
                    placeholder="Repeat password"
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>

              {/* Dynamic Role Fields: PATIENT */}
              {registerForm.role === 'PATIENT' && (
                <div className="p-3 bg-dark-900/80 border border-dark-700 rounded-xl space-y-3">
                  <div className="text-[11px] font-semibold text-cyan-400 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5" />
                    <span>Patient Health Profile Details</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Age</label>
                      <input
                        type="number"
                        min="1"
                        max="120"
                        value={registerForm.age}
                        onChange={(e) => setRegisterForm({ ...registerForm, age: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Gender</label>
                      <select
                        value={registerForm.gender}
                        onChange={(e) => setRegisterForm({ ...registerForm, gender: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      >
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Blood Group</label>
                      <select
                        value={registerForm.blood_group}
                        onChange={(e) => setRegisterForm({ ...registerForm, blood_group: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      >
                        {bloodGroups.map((bg) => (
                          <option key={bg} value={bg}>{bg}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Contact Phone</label>
                      <input
                        type="tel"
                        value={registerForm.phone}
                        onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                        placeholder="e.g. 9876543210"
                        className="w-full px-2.5 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Preferred Department</label>
                      <select
                        value={registerForm.department}
                        onChange={(e) => setRegisterForm({ ...registerForm, department: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      >
                        {departments.map((dept) => (
                          <option key={dept} value={dept}>{dept}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic Role Fields: DOCTOR */}
              {registerForm.role === 'DOCTOR' && (
                <div className="p-3 bg-dark-900/80 border border-dark-700 rounded-xl space-y-3">
                  <div className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1.5">
                    <Stethoscope className="w-3.5 h-3.5" />
                    <span>Doctor Credentials</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Department</label>
                      <select
                        value={registerForm.department}
                        onChange={(e) => setRegisterForm({ ...registerForm, department: e.target.value, specialization: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      >
                        {departments.map((dept) => (
                          <option key={dept} value={dept}>{dept}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Specialization</label>
                      <input
                        type="text"
                        value={registerForm.specialization}
                        onChange={(e) => setRegisterForm({ ...registerForm, specialization: e.target.value })}
                        placeholder="e.g. Cardiology"
                        className="w-full px-2.5 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-gray-400 mb-1">Experience (Yrs)</label>
                      <input
                        type="number"
                        min="0"
                        max="50"
                        value={registerForm.experience_years}
                        onChange={(e) => setRegisterForm({ ...registerForm, experience_years: e.target.value })}
                        className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic Role Fields: NURSE & RECEPTIONIST */}
              {(registerForm.role === 'NURSE' || registerForm.role === 'RECEPTIONIST') && (
                <div className="p-3 bg-dark-900/80 border border-dark-700 rounded-xl">
                  <label className="block text-[10px] text-gray-400 mb-1">Assigned Department</label>
                  <select
                    value={registerForm.department}
                    onChange={(e) => setRegisterForm({ ...registerForm, department: e.target.value })}
                    className="w-full px-2.5 py-1.5 bg-dark-800 border border-dark-600 rounded-lg text-xs text-white"
                  >
                    {departments.map((dept) => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Submit Register Button */}
              <button
                type="submit"
                disabled={registerLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs rounded-xl transition-all shadow-md shadow-cyan-600/20 disabled:opacity-60 flex items-center justify-center gap-2 cursor-pointer mt-2"
              >
                {registerLoading ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    <span>Create Account & Sign In</span>
                  </>
                )}
              </button>
            </form>
          </div>
        )}

      </div>
    </div>
  );
}
