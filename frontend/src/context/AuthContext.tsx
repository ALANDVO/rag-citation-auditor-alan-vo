import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile } from '../types';
import { api } from '../api/client';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  loginDemo: (role: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  loginDemo: async () => {},
  logout: async () => {},
  refreshProfile: async () => {}
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = async () => {
    try {
      const profile = await api.getProfile();
      if (profile.is_authenticated) {
        setUser(profile);
      } else {
        // Auto-login to demo-analyst in local demo mode if unauthenticated
        try {
          const demo = await api.demoLogin('analyst');
          setUser(demo);
        } catch {
          setUser(profile);
        }
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const loginDemo = async (role: string) => {
    setIsLoading(true);
    try {
      const demo = await api.demoLogin(role);
      setUser(demo);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await api.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, loginDemo, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
