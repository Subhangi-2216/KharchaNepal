import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode'; // Install if needed: npm install jwt-decode

interface AuthContextType {
  token: string | null;
  userId: number | null; // Or string, depending on your user ID type
  isAuthenticated: boolean;
  isLoading: boolean; // To handle initial check
  login: (newToken: string) => void;
  logout: () => void;
}

interface DecodedToken {
  sub: string; // Assuming email is in 'sub'
  user_id: number; // Assuming user_id is in the token payload
  exp: number;
  // Add other payload fields if necessary
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start loading initially

  // Check localStorage on initial load
  useEffect(() => {
    console.log("AuthProvider: Checking localStorage for token...");
    try {
      const storedToken = localStorage.getItem('accessToken');
      if (storedToken) {
        // Basic validation: check if token is expired
        const decoded = jwtDecode<DecodedToken>(storedToken);
        if (decoded.exp * 1000 > Date.now()) {
          console.log("AuthProvider: Valid token found in storage.", decoded);
          setToken(storedToken);
          setUserId(decoded.user_id); // Extract user ID
        } else {
          console.log("AuthProvider: Expired token found, removing.");
          localStorage.removeItem('accessToken');
        }
      } else {
         console.log("AuthProvider: No token found in storage.");
      }
    } catch (error) {
        console.error("AuthProvider: Error processing token from storage", error);
        localStorage.removeItem('accessToken'); // Clear invalid token
    } finally {
        setIsLoading(false); // Finished initial check
    }
  }, []);

  const login = (newToken: string) => {
    try {
        console.log("AuthProvider: login called.");
        const decoded = jwtDecode<DecodedToken>(newToken);
         if (decoded.exp * 1000 > Date.now()) {
            localStorage.setItem('accessToken', newToken);
            setToken(newToken);
            setUserId(decoded.user_id); // Set user ID from new token
            console.log("AuthProvider: Token set, user ID:", decoded.user_id);
         } else {
             console.error("AuthProvider: Attempted to login with an expired token.");
         }
    } catch (error) {
        console.error("AuthProvider: Error decoding token on login", error);
    }
  };

  const logout = () => {
    console.log("AuthProvider: logout called.");
    localStorage.removeItem('accessToken');
    setToken(null);
    setUserId(null);
    // Optionally redirect to login page here using useNavigate() if needed elsewhere
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, userId, isAuthenticated, isLoading, login, logout }}>
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