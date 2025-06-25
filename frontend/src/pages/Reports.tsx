import React, { useState, useEffect, useCallback } from 'react';
import { format, isValid, parseISO, startOfMonth, endOfMonth } from "date-fns";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";
import { 
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { CalendarIcon, Download, FileText, Info, FilterIcon, SheetIcon, FileIcon } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from '@/contexts/AuthContext'; // Import useAuth

// --- Configuration & Types ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Matches backend ExpenseReportItem schema
interface ReportDataItem {
  merchant_name: string | null;
  date: string; // Keep as ISO string (YYYY-MM-DD)
  amount: number; // Backend sends Decimal, frontend receives number
  currency: string;
  category: string | null;
}

const ALL_CATEGORIES = ["Food", "Travel", "Entertainment", "Household Bill", "Other"];

// Helper function to trigger download
const triggerBrowserDownload = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
};

// --- Component --- 
export default function ReportsPage() {
  const { token, isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const today = new Date();
  const [startDate, setStartDate] = useState<Date | undefined>(startOfMonth(today));
  const [endDate, setEndDate] = useState<Date | undefined>(endOfMonth(today));
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]); 
  
  // Re-add state for report data and loading/error
  const [reportData, setReportData] = useState<ReportDataItem[] | null>(null);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false); 
  
  // Keep state for initial check (optional)
  const [isLoadingCheck, setIsLoadingCheck] = useState(true);
  // const [userHasExpenses, setUserHasExpenses] = useState(false); // Can be kept or removed

  // --- Initial Check (Optional) ---
  useEffect(() => {
    const checkExpenses = async () => {
      if (!token || !isAuthenticated) {
         setIsLoadingCheck(false);
         return; 
      }
      setIsLoadingCheck(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/expenses/has_any`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        // Process response if needed
      } catch (error) {
        console.error("Error checking expenses:", error);
      } finally {
        setIsLoadingCheck(false);
      }
    };

    if (!isAuthLoading) {
        checkExpenses();
    }
  }, [token, isAuthenticated, isAuthLoading]);

  // --- Re-add Data Fetching --- 
  const fetchReportData = useCallback(async () => {
    if (!startDate || !endDate) {
      toast.error("Please select both start and end dates.");
      return;
    }
    if (startDate > endDate) {
      toast.error("Start date cannot be after end date.");
      return;
    }
     if (!token || !isAuthenticated) {
      setDataError("Authentication error. Please log in again.");
      setReportData(null);
      return;
    }

    setIsLoadingData(true);
    setDataError(null);
    setReportData(null); // Clear previous data

    const params = new URLSearchParams({
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
    });
    if (selectedCategories.length > 0) {
        params.append('category', selectedCategories.join(','));
    }

    const apiUrl = `${API_BASE_URL}/api/reports/data?${params.toString()}`;

    try {
      const response = await fetch(apiUrl, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch report data' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: ReportDataItem[] = await response.json();
      setReportData(data); // Set the fetched data
      if (data.length === 0) {
          toast.info("No expenses found for the selected criteria.");
      } else {
          toast.success("Report data loaded successfully. You can now download.");
      }

    } catch (error: any) {
      console.error("Failed to fetch report data:", error);
      const errorMsg = error.message || 'Could not fetch report data. Please try again.';
      setDataError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoadingData(false);
    }
  }, [startDate, endDate, selectedCategories, token, isAuthenticated]);

  // --- Download Handling ---
  const handleDownload = async (formatType: 'csv' | 'pdf') => {
    // Keep existing validations for dates and auth
    if (!startDate || !endDate || !token || !isAuthenticated) {
      toast.error("Cannot download: Ensure dates are selected and you are logged in.");
      return;
    }
     if (startDate > endDate) {
      toast.error("Cannot download: Start date cannot be after end date.");
      return;
    }
    // Optional: Check if data was generated first
    // if (!reportData) {
    //    toast.error("Please generate the report data first before downloading.");
    //    return;
    // }
    if (isDownloading) return; 

    setIsDownloading(true);
    toast.info(`Generating ${formatType.toUpperCase()} report...`);

    // Construct URL with same parameters used for fetching data
    const params = new URLSearchParams({
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
    });
    if (selectedCategories.length > 0) {
        params.append('category', selectedCategories.join(','));
    }

    const apiUrl = `${API_BASE_URL}/api/reports/download/${formatType}?${params.toString()}`;

    try {
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
         if (response.status === 404) {
             const errorData = await response.json().catch(() => ({ detail: 'No data found for the selected criteria.' }));
             throw new Error(errorData.detail);
         } else {
             const errorData = await response.json().catch(() => ({ detail: 'Failed to generate report' }));
             throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
         }
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `expense_report_${format(startDate, 'yyyyMMdd')}_to_${format(endDate, 'yyyyMMdd')}.${formatType}`; // Default filename
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/i);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1]; // Use filename from backend if provided
        }
      }

      triggerBrowserDownload(blob, filename);
      toast.success("Report downloaded successfully!");

    } catch (error: any) {
      console.error(`Failed to download ${formatType.toUpperCase()} report:`, error);
      toast.error(`Download failed: ${error.message || 'Please try again.'}`);
    } finally {
      setIsDownloading(false);
    }
  };

  // --- Render Logic ---

  if (isAuthLoading || isLoadingCheck) {
    // ... (Skeleton loading remains the same) ...
     return (
      <div className="space-y-6 p-4 md:p-6 animate-pulse">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-8 w-2/3" />
        <Card><CardContent className="p-6"><Skeleton className="h-40 w-full" /></CardContent></Card>
        {/* Add skeleton for preview card */}
        <Card><CardContent className="p-6"><Skeleton className="h-64 w-full" /></CardContent></Card> 
      </div>
    );
  }

  if (!isAuthenticated) {
    // ... (Not authenticated message remains the same) ...
     return (
           <div className="p-6 text-center">
               <p className="text-lg text-destructive">Please log in to view and generate reports.</p>
           </div>
       );
  }
  
  return (
    <div className="space-y-6 p-4 md:p-6">
      <h1 className="text-3xl font-bold tracking-tight">Generate Expense Report</h1>
      <p className="text-muted-foreground">
        Select your desired date range and categories to generate and download a report.
      </p>

      {/* --- Filters Card --- */} 
      <Card>
        <CardHeader>
          <CardTitle>Report Filters</CardTitle>
          <CardDescription>Choose the criteria for your report.</CardDescription>
        </CardHeader>
        {/* Adjusted grid columns slightly to fit generate button */}
        <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"> 
          {/* Start Date */} 
          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant={"outline"}
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !startDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {startDate ? format(startDate, "PPP") : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={startDate}
                  onSelect={setStartDate}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* End Date */} 
          <div className="space-y-2">
            <Label htmlFor="end-date">End Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant={"outline"}
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !endDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {endDate ? format(endDate, "PPP") : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={endDate}
                  onSelect={setEndDate}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* Categories */} 
          <div className="space-y-2">
            <Label htmlFor="categories">Categories (Optional)</Label>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-start">
                  <FilterIcon className="mr-2 h-4 w-4" />
                  {selectedCategories.length === 0
                    ? "All Categories"
                    : selectedCategories.length === 1
                    ? selectedCategories[0]
                    : `${selectedCategories.length} categories selected`}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                 <DropdownMenuLabel>Select Categories</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {ALL_CATEGORIES.map((category) => (
                    <DropdownMenuCheckboxItem
                      key={category}
                      checked={selectedCategories.includes(category)}
                      onCheckedChange={() => {
                        setSelectedCategories(current => 
                          current.includes(category) 
                            ? current.filter(c => c !== category)
                            : [...current, category]
                        );
                      }}
                    >
                      {category}
                    </DropdownMenuCheckboxItem>
                  ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
           
          {/* Re-add Generate Button */}
           <div className="space-y-2 flex items-end">
             <Button onClick={fetchReportData} className="w-full" disabled={isLoadingData}>
                {isLoadingData ? "Loading Data..." : "Generate Report Data"}
             </Button>
           </div>
        </CardContent>
         {/* Removed download buttons from here */}
         <CardFooter className="flex justify-end"> 
             {/* Footer is now empty */}
         </CardFooter>
      </Card>

      {/* --- Re-add Report Preview & Download Card --- */} 
      <Card>
        <CardHeader>
          <CardTitle>Report Preview & Download</CardTitle>
          <CardDescription>Review the data and download your report.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingData && ( // Show skeleton loader while fetching data
              <div className="space-y-2">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
              </div>
          )}
          {dataError && !isLoadingData && (
              <p className="text-center text-destructive">Error: {dataError}</p>
          )}
          {!isLoadingData && reportData && reportData.length > 0 && (
            <div className="overflow-x-auto border rounded-md">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Merchant</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Currency</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>{item.date}</TableCell>
                      <TableCell>{item.merchant_name || 'N/A'}</TableCell>
                      <TableCell>{item.category || 'N/A'}</TableCell>
                      <TableCell className="text-right">{parseFloat(String(item.amount)).toFixed(2)}</TableCell>
                      <TableCell>{item.currency}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          {!isLoadingData && reportData && reportData.length === 0 && (
              <p className="text-center text-muted-foreground">No expenses found matching your criteria.</p>
          )}
           {!isLoadingData && !reportData && !dataError && (
               <p className="text-center text-muted-foreground">Click "Generate Report Data" above to see a preview.</p>
           )}
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row justify-end gap-2 pt-4 border-t">
            <Button 
                variant="default" // Keep the blue color
                onClick={() => handleDownload('csv')} 
                // Disable if downloading OR if no data has been successfully loaded
                disabled={isDownloading || isLoadingData || !reportData || reportData.length === 0} 
            >
                <SheetIcon className="mr-2 h-4 w-4" />
                {isDownloading ? "Generating..." : "Download CSV"}
            </Button>
            <Button 
                variant="default" // Keep the blue color
                onClick={() => handleDownload('pdf')} 
                 // Disable if downloading OR if no data has been successfully loaded
                disabled={isDownloading || isLoadingData || !reportData || reportData.length === 0}
            >
                <FileIcon className="mr-2 h-4 w-4" />
                {isDownloading ? "Generating..." : "Download PDF"}
            </Button>
        </CardFooter>
      </Card>

    </div>
  );
}
