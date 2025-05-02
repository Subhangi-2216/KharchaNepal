import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { loginSchema, LoginFormData } from '@/lib/validators/auth';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from "@/lib/utils";
import { CreditCard } from "lucide-react";

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

      // Create form data object for FastAPI OAuth2 compatibility
      const formData = new URLSearchParams();
      formData.append('username', data.email); // FastAPI OAuth2 expects 'username'
      formData.append('password', data.password);

      const response = await axios.post(`${API_BASE_URL}/api/auth/login`,
        formData.toString(), // Convert to string
        {
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
    <div className="flex items-center justify-center min-h-screen bg-muted/30">
      <div className="w-full max-w-md px-4">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary/10 p-3 rounded-full mb-4">
            <CreditCard className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">KharchaNP</h1>
          <p className="text-muted-foreground mt-1">Your personal expense tracker</p>
        </div>

        <Card className="w-full border-border/40 shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">Login</CardTitle>
            <CardDescription className="text-center">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  autoComplete="email"
                  {...register('email')}
                  className={cn(errors.email && "border-destructive focus-visible:ring-destructive")}
                />
                {errors.email && (
                  <p className="text-destructive text-sm flex items-center gap-1">
                    <span className="h-1 w-1 rounded-full bg-destructive inline-block"></span>
                    {errors.email.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link to="#" className="text-xs text-primary hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  {...register('password')}
                  className={cn(errors.password && "border-destructive focus-visible:ring-destructive")}
                />
                {errors.password && (
                  <p className="text-destructive text-sm flex items-center gap-1">
                    <span className="h-1 w-1 rounded-full bg-destructive inline-block"></span>
                    {errors.password.message}
                  </p>
                )}
              </div>

              {errorMessage && (
                <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                  {errorMessage}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Logging in...</span>
                  </div>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Button variant="outline" type="button" className="flex items-center gap-2">
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Google
              </Button>
              <Button variant="outline" type="button" className="flex items-center gap-2">
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16.365 1.43c0 1.14-.493 2.27-1.177 3.08-.744.9-1.99 1.57-2.987 1.57-.12 0-.23-.02-.3-.03-.01-.06-.04-.22-.04-.39 0-1.15.572-2.27 1.206-2.98.804-.94 2.142-1.64 3.248-1.68.03.13.05.28.05.43zm4.565 15.71c-.03.07-.463 1.58-1.518 3.12-.945 1.34-1.94 2.71-3.43 2.71-1.517 0-1.9-.88-3.63-.88-1.698 0-2.302.91-3.67.91-1.377 0-2.332-1.26-3.428-2.8-1.287-1.82-2.323-4.63-2.323-7.28 0-4.28 2.797-6.55 5.552-6.55 1.448 0 2.675.95 3.6.95.865 0 2.222-1.01 3.902-1.01.613 0 2.886.06 4.374 2.19-.13.09-2.383 1.37-2.383 4.19 0 3.26 2.854 4.42 2.955 4.45z" />
                </svg>
                Apple
              </Button>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-center gap-2 border-t p-6">
            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link to="/register" className="text-primary font-medium hover:underline">
                Sign up
              </Link>
            </p>
            <p className="text-xs text-muted-foreground">
              By continuing, you agree to our{" "}
              <Link to="#" className="hover:underline">Terms of Service</Link>
              {" "}and{" "}
              <Link to="#" className="hover:underline">Privacy Policy</Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;