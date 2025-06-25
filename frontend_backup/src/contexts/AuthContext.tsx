import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';
import axios from 'axios';

// User interface
interface User {
  id: number;
  email: string;
  name: string;
  avatar_url?: string;
}

interface AuthContextType {
  token: string | null;
  userId: number | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (newToken: string) => void;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

interface DecodedToken {
  sub: string; // Email is in 'sub'
  user_id: number;
  name?: string;
  exp: number;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch user data from API
  const fetchUserData = async (token: string) => {
    try {
      // Try to get user data from the API
      const response = await axios.get(`${API_BASE_URL}/api/auth/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data) {
        setUser({
          id: response.data.id,
          email: response.data.email,
          name: response.data.full_name || 'User',
          avatar_url: response.data.avatar_url
        });
      }
    } catch (error) {
      console.error("Failed to fetch user data:", error);

      // If the endpoint doesn't exist or returns an error, try to extract basic info from the token
      try {
        const decoded = jwtDecode<DecodedToken>(token);
        setUser({
          id: decoded.user_id,
          email: decoded.sub,
          name: decoded.name || 'User',
          avatar_url: undefined
        });
      } catch (tokenError) {
        console.error("Failed to extract user data from token:", tokenError);
        // Set a minimal user object to prevent UI errors
        setUser({
          id: 0,
          email: 'user@example.com',
          name: 'User',
          avatar_url: undefined
        });
      }
    }
  };

  // Check localStorage on initial load
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('accessToken');
        if (storedToken) {
          // Basic validation: check if token is expired
          const decoded = jwtDecode<DecodedToken>(storedToken);
          if (decoded.exp * 1000 > Date.now()) {
            setToken(storedToken);
            setUserId(decoded.user_id);

            // Fetch user data
            await fetchUserData(storedToken);
          } else {
            localStorage.removeItem('accessToken');
          }
        }
      } catch (error) {
        console.error("Error processing token from storage", error);
        localStorage.removeItem('accessToken');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (newToken: string) => {
    try {
      const decoded = jwtDecode<DecodedToken>(newToken);
      if (decoded.exp * 1000 > Date.now()) {
        localStorage.setItem('accessToken', newToken);
        setToken(newToken);
        setUserId(decoded.user_id);

        // Fetch user data after login
        await fetchUserData(newToken);
      } else {
        console.error("Attempted to login with an expired token.");
      }
    } catch (error) {
      console.error("Error decoding token on login", error);
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    setToken(null);
    setUserId(null);
    setUser(null);
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider
      value={{
        token,
        userId,
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        updateUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};