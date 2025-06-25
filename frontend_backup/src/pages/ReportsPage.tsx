import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { format, subDays } from 'date-fns';
import { DateRange } from "react-day-picker";
import qs from 'qs'; // For formatting query parameters
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Download, CalendarDays } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, Sector } from 'recharts'; // Import chart components

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Categories matching backend Enum
const allCategories = ["Food", "Travel", "Entertainment", "Household Bill", "Other"] as const;
type Category = typeof allCategories[number];

// Type for report data items (matching backend/reports/schemas.py)
interface ReportItem {
    merchant_name: string;
    date: string; // Date as string from backend
    amount: number;
    currency: string;
    category: Category;
}

// Function to fetch report data
const fetchReportData = async (filters: { start_date?: string; end_date?: string; category?: string[] }): Promise<ReportItem[]> => {
    if (!filters.start_date || !filters.end_date) {
        // Don't fetch if date range isn't fully selected
        return [];
    }
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('No authentication token found.');

    const params = {
        start_date: filters.start_date,
        end_date: filters.end_date,
        // Join categories array into comma-separated string for query param
        category: filters.category?.join(',') || undefined 
    };

    const response = await axios.get(`${API_BASE_URL}/api/reports/data`, {
        headers: { Authorization: `Bearer ${token}` },
        params: params,
        // Use qs to handle array formatting if needed, though FastAPI handles comma-separated by default
        // paramsSerializer: params => qs.stringify(params, { arrayFormat: 'comma' }) 
    });
    return Array.isArray(response.data) ? response.data : [];
};

// Function to generate download URL
const getDownloadUrl = (format: 'csv' | 'pdf', filters: { start_date?: string; end_date?: string; category?: string[] }): string => {
    if (!filters.start_date || !filters.end_date) return '#'; // Prevent download if dates invalid
    
    const params = {
        start_date: filters.start_date,
        end_date: filters.end_date,
        category: filters.category?.join(',') || undefined
    };
    // Remove undefined params
    const cleanParams = Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== undefined));
    const queryString = qs.stringify(cleanParams);

    return `${API_BASE_URL}/api/reports/download/${format}?${queryString}`;
};

// Helper function to process data for category chart
const processDataForCategoryChart = (data: ReportItem[]) => {
    const categoryTotals = data.reduce((acc, item) => {
        acc[item.category] = (acc[item.category] || 0) + item.amount;
        return acc;
    }, {} as Record<Category, number>);

    return Object.entries(categoryTotals).map(([name, value]) => ({ name, value }));
};

const ReportsPage: React.FC = () => {
    // State for filters
    const [dateRange, setDateRange] = useState<DateRange | undefined>({
        from: subDays(new Date(), 29), // Default to last 30 days
        to: new Date(),
    });
    const [selectedCategories, setSelectedCategories] = useState<Category[]>([]); // Start with empty or all selected?
    const [triggerFetch, setTriggerFetch] = useState(false); // Trigger query manually

    // Derived filter values for the query
    const queryFilters = {
        start_date: dateRange?.from ? format(dateRange.from, 'yyyy-MM-dd') : undefined,
        end_date: dateRange?.to ? format(dateRange.to, 'yyyy-MM-dd') : undefined,
        category: selectedCategories.length > 0 ? selectedCategories : undefined,
    };

    // Fetch report data - enabled only when triggerFetch is true and dates are set
    const { data: reportData = [], isLoading, error, refetch } = useQuery<ReportItem[], Error>({
        queryKey: ['reportData', queryFilters], 
        queryFn: () => fetchReportData(queryFilters),
        enabled: triggerFetch && !!queryFilters.start_date && !!queryFilters.end_date, // Only run when enabled
        staleTime: 5 * 60 * 1000, // Keep data fresh for 5 mins
    });

    const handleGenerateReport = () => {
        setTriggerFetch(true); // Enable the query
        refetch(); // Explicitly trigger refetch with current filters
    };

    const handleCategoryChange = (category: Category, checked: boolean) => {
        setSelectedCategories(prev => 
            checked 
                ? [...prev, category] 
                : prev.filter(c => c !== category)
        );
        setTriggerFetch(false); // Require explicit generation after filter change
    };

    const handleStartDateChange = (date: Date | undefined) => {
        setDateRange(prev => ({ from: date, to: prev?.to }));
        setTriggerFetch(false);
    };

    const handleEndDateChange = (date: Date | undefined) => {
        setDateRange(prev => ({ from: prev?.from, to: date }));
        setTriggerFetch(false);
    };

    // Prepare data for chart
    const categoryChartData = processDataForCategoryChart(reportData);
    // Define colors for pie chart
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

    return (
        <div className="container mx-auto py-8 space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Reports</h1>

            {/* Filter Section */}
            <Card>
                <CardHeader>
                    <CardTitle>Generate Report</CardTitle>
                    <CardDescription>Select filters and generate or download your expense report.</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Date Range Pickers (Separate Popovers) */}
                    <div className="space-y-2">
                        <Label>Date Range</Label>
                        <div className="grid grid-cols-2 gap-2">
                            {/* Start Date */}
                            <Popover>
                                <PopoverTrigger asChild>
                                <Button
                                    variant={"outline"}
                                    className={cn(
                                    "w-full justify-start text-left font-normal",
                                    !dateRange?.from && "text-muted-foreground"
                                    )}
                                >
                                    <CalendarDays className="mr-2 h-4 w-4" />
                                    {dateRange?.from ? format(dateRange.from, "PPP") : <span>Start date</span>}
                                </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                    mode="single"
                                    selected={dateRange?.from}
                                    onSelect={handleStartDateChange}
                                    initialFocus
                                    // disabled={(date) => date > (dateRange?.to || new Date()) || date < new Date("1900-01-01")}
                                />
                                </PopoverContent>
                            </Popover>
                            {/* End Date */}
                             <Popover>
                                <PopoverTrigger asChild>
                                <Button
                                    variant={"outline"}
                                    className={cn(
                                    "w-full justify-start text-left font-normal",
                                    !dateRange?.to && "text-muted-foreground"
                                    )}
                                >
                                    <CalendarDays className="mr-2 h-4 w-4" />
                                    {dateRange?.to ? format(dateRange.to, "PPP") : <span>End date</span>}
                                </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                    mode="single"
                                    selected={dateRange?.to}
                                    onSelect={handleEndDateChange}
                                    // disabled={(date) => date < (dateRange?.from || new Date("1900-01-01"))}
                                    initialFocus
                                />
                                </PopoverContent>
                            </Popover>
                        </div>
                        {dateRange?.from && dateRange?.to && dateRange.from > dateRange.to && (
                            <p className="text-sm text-red-600">Start date cannot be after end date.</p>
                        )}
                    </div>
                    
                    {/* Category Checkboxes */}
                    <div className="space-y-2">
                        <Label>Categories (Optional)</Label>
                        <div className="space-y-1.5 pt-1">
                            {allCategories.map(cat => (
                                <div key={cat} className="flex items-center space-x-2">
                                    <Checkbox 
                                        id={`cat-${cat}`}
                                        checked={selectedCategories.includes(cat)}
                                        onCheckedChange={(checked) => handleCategoryChange(cat, !!checked)}
                                    />
                                    <label
                                        htmlFor={`cat-${cat}`}
                                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                    >
                                        {cat}
                                    </label>
                                </div>
                            ))}
                             <Button variant="link" size="sm" className="p-0 h-auto" onClick={() => setSelectedCategories([])}>Clear</Button> 
                        </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="space-y-3 md:pt-6">
                        <Button onClick={handleGenerateReport} disabled={isLoading || !dateRange?.from || !dateRange?.to} className="w-full">
                            {isLoading ? "Generating..." : "Generate Report Preview"}
                        </Button>
                        <div className="grid grid-cols-2 gap-2">
                            <Button 
                                variant="outline" 
                                asChild // Use asChild to make the button act like a link
                                disabled={!triggerFetch || isLoading || reportData.length === 0 || !dateRange?.from || !dateRange?.to}
                            >
                               <a href={getDownloadUrl('csv', queryFilters)} download={`expense_report_${queryFilters.start_date}_to_${queryFilters.end_date}.csv`}>
                                    <Download className="mr-2 h-4 w-4" /> CSV
                                </a>
                            </Button>
                            <Button 
                                variant="outline" 
                                asChild 
                                disabled={!triggerFetch || isLoading || reportData.length === 0 || !dateRange?.from || !dateRange?.to}
                            >
                                <a href={getDownloadUrl('pdf', queryFilters)} download={`expense_report_${queryFilters.start_date}_to_${queryFilters.end_date}.pdf`}>
                                    <Download className="mr-2 h-4 w-4" /> PDF
                                </a>
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Report Preview Section */}
            {triggerFetch && (
                <Card>
                    <CardHeader>
                        <CardTitle>Report Preview</CardTitle>
                        {reportData.length > 0 && (
                            <CardDescription>
                                Showing {reportData.length} expenses from {queryFilters.start_date} to {queryFilters.end_date}
                                {queryFilters.category ? ` for categories: ${queryFilters.category.join(', ')}` : '.'}
                            </CardDescription>
                        )}
                    </CardHeader>
                    <CardContent>
                        {isLoading && <p className="p-4 text-center">Loading report data...</p>}
                        {!isLoading && error && <p className="p-4 text-red-500 text-center">Error loading report: {error.message}</p>}
                        {!isLoading && !error && (
                            <div className="space-y-6">
                                {/* Chart Section */}
                                {reportData.length > 0 && categoryChartData.length > 0 && (
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={categoryChartData}
                                                    cx="50%"
                                                    cy="50%"
                                                    labelLine={false}
                                                    // label={renderCustomizedLabel} // Add custom label if needed
                                                    outerRadius={100}
                                                    fill="#8884d8"
                                                    dataKey="value"
                                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                                >
                                                    {categoryChartData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                    ))}
                                                </Pie>
                                                <Tooltip formatter={(value: number) => `NPR ${value.toFixed(2)}`} />
                                                <Legend />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}

                                {/* Data Table Section */}
                                <div className="border rounded-lg overflow-hidden">
                                    <Table>
                                        <TableCaption className="py-4">
                                            {reportData.length === 0 ? "No expenses found for the selected criteria." : "Filtered expense details."} 
                                        </TableCaption>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead className="w-[150px]">Date</TableHead>
                                                <TableHead>Merchant</TableHead>
                                                <TableHead>Category</TableHead>
                                                <TableHead className="text-right">Amount</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {reportData.length === 0 ? (
                                                <TableRow>
                                                    <TableCell colSpan={4} className="h-24 text-center">
                                                        No expenses found.
                                                    </TableCell>
                                                </TableRow>
                                            ) : (
                                                reportData.map((item, index) => (
                                                    <TableRow key={index}>
                                                        <TableCell>{item.date ? format(new Date(item.date), 'PPP') : 'N/A'}</TableCell>
                                                        <TableCell className="font-medium">{item.merchant_name}</TableCell>
                                                        <TableCell>{item.category}</TableCell>
                                                        <TableCell className="text-right">
                                                            {item.currency} {typeof item.amount === 'number' ? item.amount.toFixed(2) : 'N/A'}
                                                        </TableCell>
                                                    </TableRow>
                                                ))
                                            )}
                                        </TableBody>
                                    </Table>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default ReportsPage; 