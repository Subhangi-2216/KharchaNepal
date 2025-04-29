import { z } from 'zod';

// Schema for Login Form
export const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(1, { message: 'Password is required' }), // Basic check, backend handles complexity if needed
});

export type LoginFormData = z.infer<typeof loginSchema>;


// Schema for Registration Form
export const registerSchema = z.object({
  name: z.string().min(1, { message: 'Name is required' }),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters long' }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'], // Point error to the confirmation field
});

export type RegisterFormData = z.infer<typeof registerSchema>; 