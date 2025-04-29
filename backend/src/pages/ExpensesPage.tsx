import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query'; // For fetching data
import axios from 'axios';

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import AddExpenseForm from '@/components/expenses/AddExpenseForm'; // Import the form
// Import Table components from shadcn if needed for displaying expenses
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Placeholder type for expense data (replace with actual type from backend schemas later)
interface Expense {
    id: number;
    merchant_name: string;
    date: string; // Or Date object
    amount: number;
    category: string;
    currency: string;
}

// Function to fetch expenses (requires GET /api/expenses endpoint)
const fetchExpenses = async (): Promise<Expense[]> => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('No authentication token found');

    // Replace with your actual GET expenses endpoint
    const response = await axios.get(`${API_BASE_URL}/api/expenses`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data; // Assuming backend returns an array of expenses
};

const ExpensesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);

    // Fetch expenses using React Query
    const { data: expenses, isLoading, error } = useQuery<Expense[], Error>(
        { 
            queryKey: ['expenses'], 
            queryFn: fetchExpenses, 
            // Add options like staleTime, cacheTime if needed
            // retry: false // Optional: disable retries on error
        }
    );

    const handleAddSuccess = () => {
        setIsAddExpenseOpen(false); // Close the dialog
        // Invalidate the expenses query to trigger a refetch
        queryClient.invalidateQueries({ queryKey: ['expenses'] });
    };

    return (
        <div className="container mx-auto py-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Expenses</h1>
                <Dialog open={isAddExpenseOpen} onOpenChange={setIsAddExpenseOpen}>
                    <DialogTrigger asChild>
                        <Button>Add New Expense</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Add Manual Expense</DialogTitle>
                            <DialogDescription>
                                Fill in the details for your new expense.
                            </DialogDescription>
                        </DialogHeader>
                        <AddExpenseForm 
                            onSuccess={handleAddSuccess} 
                            onCancel={() => setIsAddExpenseOpen(false)}
                        />
                    </DialogContent>
                </Dialog>
            </div>

            {/* Display Expenses List */}
            <div className="bg-white shadow rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-4">Expense List</h2>
                {isLoading && <p>Loading expenses...</p>}
                {error && <p className="text-red-500">Error fetching expenses: {error.message}</p>}
                {!isLoading && !error && (
                    expenses && expenses.length > 0 ? (
                        // Placeholder: Render your expense list here (e.g., using a Table)
                        <ul>
                            {expenses.map((exp) => (
                                <li key={exp.id} className="border-b py-2">
                                    {exp.date} - {exp.merchant_name} - {exp.category} - {exp.currency} {exp.amount}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p>No expenses recorded yet. Click 'Add New Expense' to start.</p>
                    )
                )}
            </div>
        </div>
    );
};

export default ExpensesPage; 