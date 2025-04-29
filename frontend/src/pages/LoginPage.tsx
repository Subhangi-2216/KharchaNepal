import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

import { Button } from "@/components/ui/button"; // Assuming shadcn setup
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { loginSchema, LoginFormData } from '@/lib/validators/auth';
import { useAuth } from '@/contexts/AuthContext'; // Import useAuth

// Ensure VITE_API_BASE_URL is set in your .env file
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // Default if not set

const LoginPage: React.FC = (): JSX.Element => {
  const navigate = useNavigate();
  const { login } = useAuth(); // Get the login function from context
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // IMPORTANT: FastAPI default token URL is often /token or /auth/jwt/login
      // Adjust the URL path based on your actual backend API endpoint
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username: data.email, // FastAPI default OAuth2 expects 'username'
        password: data.password,
      }, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' } // FastAPI standard for form data
      });

      // Use the login function from context
      if (response.data.access_token) {
        login(response.data.access_token);
        console.log('Login successful, token passed to AuthContext');
        navigate('/home'); // Redirect to home page on success
      } else {
         // Handle case where token is missing in response
         throw new Error('Login successful, but no token received.');
      }
    } catch (error) {
      console.error('Login failed:', error);
      if (axios.isAxiosError(error) && error.response) {
        // Handle specific backend errors (e.g., 401 Unauthorized)
        if (error.response.status === 401 || error.response.status === 400) {
            setErrorMessage('Invalid email or password.');
        } else {
            setErrorMessage(`An error occurred: ${error.response.data.detail || error.message}`);
        }
      } else if (error instanceof Error) {
           setErrorMessage(error.message); // Show specific error if token was missing
      } else {
        setErrorMessage('An unexpected error occurred. Please try again.');
      }
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Login</CardTitle>
          <CardDescription>Enter your email and password to access your account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                {...register('email')}
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && <p className="text-red-500 text-sm">{errors.email.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="********"
                {...register('password')}
                className={errors.password ? 'border-red-500' : ''}
              />
              {errors.password && <p className="text-red-500 text-sm">{errors.password.message}</p>}
            </div>
            {errorMessage && (
              <p className="text-red-500 text-sm font-medium text-center">{errorMessage}</p>
            )}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-center text-sm">
          <p>Don't have an account? <Link to="/register" className="text-blue-600 hover:underline">Register here</Link></p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage; 