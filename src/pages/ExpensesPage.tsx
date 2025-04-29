import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query'; // For fetching data
import axios from 'axios';
import { format } from 'date-fns'; // Import format for date display

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import AddExpenseForm from '@/components/expenses/AddExpenseForm'; // Import the form
// Import Table components from shadcn
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
// TODO: Import Table components from shadcn for displaying expenses
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// TODO: Replace with actual type definition based on backend/expenses/schemas.py Expense schema
interface Expense {
    id: number;
    merchant_name: string;
    date: string; // Backend returns date string
    amount: number; // Use number, formatting done during display
    category: string;
    currency: string;
}

// Function to fetch expenses (requires GET /api/expenses endpoint)
const fetchExpenses = async (): Promise<Expense[]> => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('No authentication token found');

    // TODO: Implement GET /api/expenses endpoint in the backend
    const response = await axios.get(`${API_BASE_URL}/api/expenses`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    // TODO: Ensure backend returns an array of expenses matching the Expense interface
    return response.data || []; // Return empty array if data is null/undefined
};

const ExpensesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);

    // Fetch expenses using React Query
    const { data: expenses = [], isLoading, error, isFetching } = useQuery<Expense[], Error>(
        { 
            queryKey: ['expenses'], 
            queryFn: fetchExpenses, 
            // Placeholder data while loading or if fetch fails initially?
            // placeholderData: [], 
             // Keep previous data while loading new? Useful for pagination
            // keepPreviousData: true, 
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
                        <Button disabled={isFetching}>Add New Expense</Button>
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

            {/* Display Expenses List using shadcn Table */}
            <div className="bg-white shadow rounded-lg overflow-hidden"> 
                {/* Added overflow-hidden for rounded corners with table */}
                {isLoading && <p className="p-4">Loading expenses...</p>}
                {error && <p className="p-4 text-red-500">Error fetching expenses: {error.message}</p>}
                {!isLoading && !error && (
                    <Table>
                        <TableCaption className="py-4">
                            {expenses.length === 0 
                                ? "No expenses recorded yet. Click 'Add New Expense' to start."
                                : "A list of your recent expenses."
                            }
                        </TableCaption>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[150px]">Date</TableHead>
                                <TableHead>Merchant</TableHead>
                                <TableHead>Category</TableHead>
                                <TableHead className="text-right">Amount</TableHead>
                                {/* TODO: Add Head for Actions (Edit/Delete) */}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {expenses.length === 0 && !isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="h-24 text-center">
                                        No expenses found.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                expenses.map((exp) => (
                                    <TableRow key={exp.id}>
                                        <TableCell>{format(new Date(exp.date), 'PPP')}</TableCell> {/* Format date */}
                                        <TableCell className="font-medium">{exp.merchant_name}</TableCell>
                                        <TableCell>{exp.category}</TableCell>
                                        <TableCell className="text-right">{exp.currency} {exp.amount.toFixed(2)}</TableCell> {/* Format amount */}
                                        {/* TODO: Add Cell for Actions (Edit/Delete Buttons) */}
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                )}
            </div>
        </div>
    );
};

export default ExpensesPage; 