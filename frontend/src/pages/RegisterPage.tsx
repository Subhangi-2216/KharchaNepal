import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { registerSchema, RegisterFormData } from '@/lib/validators/auth';

// Ensure VITE_API_BASE_URL is set in your .env file
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // Default if not set

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Adjust the URL path based on your actual backend API endpoint
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        name: data.name,
        email: data.email,
        password: data.password,
        // No need to send confirmPassword to backend
      });

      console.log('Registration successful', response.data);
      // Optionally display a success message before redirecting
      navigate('/login'); // Redirect to login page on success
    } catch (error) {
      console.error('Registration failed:', error);
        if (axios.isAxiosError(error) && error.response) {
            // Handle specific backend errors (e.g., 400 Bad Request for duplicate email)
            if (error.response.status === 400) {
                // Check for specific detail messages if backend provides them
                if (error.response.data?.detail?.toLowerCase().includes('email')) {
                     setErrorMessage('Email already exists. Please use a different email or login.');
                } else {
                    setErrorMessage(`Registration failed: ${error.response.data.detail || 'Invalid input.'}`);
                }
            } else {
                setErrorMessage(`An error occurred: ${error.response.data.detail || error.message}`);
            }
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
          <CardTitle className="text-2xl font-bold">Register</CardTitle>
          <CardDescription>Create a new account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Your Name"
                {...register('name')}
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-red-500 text-sm">{errors.name.message}</p>}
            </div>
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
                placeholder="Minimum 8 characters"
                {...register('password')}
                className={errors.password ? 'border-red-500' : ''}
              />
              {errors.password && <p className="text-red-500 text-sm">{errors.password.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter password"
                {...register('confirmPassword')}
                className={errors.confirmPassword ? 'border-red-500' : ''}
              />
              {errors.confirmPassword && <p className="text-red-500 text-sm">{errors.confirmPassword.message}</p>}
            </div>
             {errorMessage && (
              <p className="text-red-500 text-sm font-medium text-center">{errorMessage}</p>
            )}
            <Button type="submit" className="w-full" disabled={isLoading}>
               {isLoading ? 'Registering...' : 'Register'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-center text-sm">
          <p>Already have an account? <Link to="/login" className="text-blue-600 hover:underline">Login here</Link></p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default RegisterPage; 