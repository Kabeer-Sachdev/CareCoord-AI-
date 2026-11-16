import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/auth';
import { wsClient } from '../services/websocket';

const QUICK_LOGIN_CREDS = {
  admin:        { email: 'admin@carecoord.demo',      password: 'Demo@1234' },
  receptionist: { email: 'reception@carecoord.demo',  password: 'Demo@1234' },
  doctor:       { email: 'doctor@carecoord.demo',     password: 'Demo@1234' },
  nurse:        { email: 'nurse@carecoord.demo',      password: 'Demo@1234' },
  patient:      { email: 'patient@carecoord.demo',    password: 'Demo@1234' },
};

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(() => authService.getUser());
  const [token, setToken] = useState(() => authService.getToken());

  // On mount, reconnect WS if already authenticated
  useEffect(() => {
    const t = authService.getToken();
    if (t) wsClient.connect(t);
    return () => {};
  }, []);

  const register = useCallback(async (userData) => {
    const data = await authService.register(userData);
    setUser(data.user);
    setToken(data.access_token);
    wsClient.connect(data.access_token);
    return data;
  }, []);

  const login = useCallback(async (emailOrUsername, password) => {
    const data = await authService.login(emailOrUsername, password);
    setUser(data.user);
    setToken(data.access_token);
    wsClient.connect(data.access_token);
    return data;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setToken(null);
    wsClient.disconnect();
  }, []);

  const quickLogin = useCallback(async (role) => {
    const creds = QUICK_LOGIN_CREDS[role];
    if (!creds) throw new Error(`Unknown role: ${role}`);
    return login(creds.email, creds.password);
  }, [login]);

  const isAuthenticated = !!token;
  const role = user?.role ?? null;

  return (
    <AuthContext.Provider value={{ user, token, role, isAuthenticated, register, login, logout, quickLogin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
