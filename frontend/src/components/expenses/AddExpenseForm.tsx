import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import axios from 'axios';
import { format } from 'date-fns';
import { CalendarDays } from 'lucide-react';

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import { manualExpenseSchema, ManualExpenseFormData } from '@/lib/validators/expense';

const categories = [
    "Food",
    "Travel",
    "Entertainment",
    "Household Bill",
    "Other"
] as const;

interface AddExpenseFormProps {
  onSuccess: () => void; 
  onCancel: () => void; 
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const AddExpenseForm: React.FC<AddExpenseFormProps> = ({ onSuccess, onCancel }) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<ManualExpenseFormData>({
    resolver: zodResolver(manualExpenseSchema),
    defaultValues: {
        merchant_name: "",
        amount: undefined,
        date: undefined,
        category: undefined,
    }
  });

  const selectedDate = watch('date');

  const onSubmit = async (data: ManualExpenseFormData) => {
    setIsLoading(true);
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            throw new Error('Authentication token not found.');
        }

        const formattedData = {
            ...data,
            date: data.date ? format(data.date, 'yyyy-MM-dd') : '' 
        };

        await axios.post(
            `${API_BASE_URL}/api/expenses/manual`,
            formattedData,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            }
        );

        toast({
            title: "Success!",
            description: "Expense added successfully.",
        });
        reset();
        onSuccess();

    } catch (error) {
        console.error('Failed to add expense:', error);
        let description = "Failed to add expense. Please try again.";
        if (axios.isAxiosError(error) && error.response) {
            if (error.response.status === 401) {
                description = "Authentication failed. Please log in again.";
            } else if (error.response.data?.detail) {
                description = typeof error.response.data.detail === 'string'
                    ? error.response.data.detail
                    : JSON.stringify(error.response.data.detail);
            }
        } else if (error instanceof Error) {
            description = error.message;
        }
        toast({
            title: "Error",
            description: description,
            variant: "destructive",
        });
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1">
        <Label htmlFor="merchant_name">Merchant Name</Label>
        <Input
          id="merchant_name"
          placeholder="e.g., Bhatbhateni Supermarket"
          {...register('merchant_name')}
          className={cn(errors.merchant_name && "border-red-500")}
        />
        {errors.merchant_name && <p className="text-sm text-red-600">{errors.merchant_name.message}</p>}
      </div>

      <div className="space-y-1">
         <Label htmlFor="date">Date</Label>
         <Popover>
            <PopoverTrigger asChild>
              <Button
                variant={"outline"}
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !selectedDate && "text-muted-foreground",
                  errors.date && "border-red-500"
                )}
              >
                <CalendarDays className="mr-2 h-4 w-4" />
                {selectedDate ? format(selectedDate, "PPP") : <span>Pick a date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={(day) => setValue('date', day as Date, { shouldValidate: true })}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        {errors.date && <p className="text-sm text-red-600">{errors.date.message}</p>}
      </div>

      <div className="space-y-1">
        <Label htmlFor="amount">Amount (NPR)</Label>
        <Input
          id="amount"
          type="number"
          step="0.01"
          placeholder="e.g., 1500.50"
          {...register('amount')}
          className={cn(errors.amount && "border-red-500")}
        />
        {errors.amount && <p className="text-sm text-red-600">{errors.amount.message}</p>}
      </div>

        <div className="space-y-1">
            <Label htmlFor="category">Category</Label>
             <Select
                onValueChange={(value) => setValue('category', value as typeof categories[number], { shouldValidate: true })}
            >
                <SelectTrigger id="category" className={cn(errors.category && "border-red-500")}>
                    <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                    {cat}
                    </SelectItem>
                ))}
                </SelectContent>
            </Select>
            {errors.category && <p className="text-sm text-red-600">{errors.category.message}</p>}
        </div>

      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Expense'}
        </Button>
      </div>
    </form>
  );
};

export default AddExpenseForm; 