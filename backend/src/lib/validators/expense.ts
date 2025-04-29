import { z } from 'zod';

// Define the allowed categories based on the backend Enum
const allowedCategories = [
    "Food",
    "Travel",
    "Entertainment",
    "Household Bill",
    "Other"
] as const; // Use 'as const' for literal types

export const manualExpenseSchema = z.object({
  merchant_name: z.string().min(1, { message: 'Merchant name is required' }),
  date: z.date({ required_error: "Please select a date" }), // Use z.date for date picker output
  amount: z.coerce // Use coerce for inputs that might start as string
    .number({ invalid_type_error: "Amount must be a number" })
    .positive({ message: 'Amount must be greater than zero' }),
  category: z.enum(allowedCategories, { required_error: "Please select a category" }),
});

export type ManualExpenseFormData = z.infer<typeof manualExpenseSchema>; 