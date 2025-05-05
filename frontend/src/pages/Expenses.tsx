import React, { useState, useRef, ChangeEvent, useEffect } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { format } from 'date-fns';
import { produce } from 'immer';

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import AddExpenseForm from '@/components/expenses/AddExpenseForm';
import DropzoneArea from '@/components/expenses/DropzoneArea';
import ScanningDialog from '@/components/expenses/ScanningDialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Plus, Search, MessageSquare, ChevronDown, ChevronUp, Send, Upload, FileText, Edit, Trash, ScanLine } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

const API_BASE_URL = ''; // This will use the same origin and proxy through Vite

function ExpenseQueryChatbot() {
  const { token } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { role: "system", content: "Hello! I'm your Expense Query Assistant. Ask me about your expenses or tell me to add a new one." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of messages when new ones are added
  useEffect(() => {
    if (messagesEndRef.current) {
      const chatContainer = messagesEndRef.current.parentElement;
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = async () => {
    const userQuery = input.trim();
    if (!userQuery || isLoading) return;

    const newUserMessage = { role: "user" as const, content: userQuery };
    setMessages(prev => [...prev, newUserMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '/api/chatbot/query';

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: userQuery })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error from chatbot API' }));
        throw new Error(errorData.detail || `Error: ${response.status}`);
      }

      const botResponseData = await response.json();
      const newSystemMessage = { role: "system" as const, content: botResponseData.data };

      // Add a small delay to make the response feel more natural
      setTimeout(() => {
        setMessages(prev => [...prev, newSystemMessage]);
        setIsLoading(false);
      }, 500);

    } catch (error: any) {
      console.error("Expense Chatbot Error:", error);
      toast.error(`Chatbot error: ${error.message}`);
      const errorSystemMessage = {
        role: "system" as const,
        content: "Sorry, I encountered an error processing your request. Please try again or contact support if the issue persists."
      };
      setMessages(prev => [...prev, errorSystemMessage]);
      setIsLoading(false);
    }
  };

  return (
    <div
      className={cn(
        "fixed transition-all duration-300 z-50",
        isExpanded
          ? "bottom-4 right-4 w-full md:w-1/3 h-[calc(100vh-6rem)]"
          : "bottom-4 right-4 w-14 h-14"
      )}
    >
      {isExpanded ? (
        <Card className="h-full flex flex-col">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <div>
              <CardTitle>Expense Query Assistant</CardTitle>
              <CardDescription>Ask about your expenses</CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsExpanded(false)}
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "system" && (
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center mr-2">
                        <Send className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div className={`max-w-[80%] rounded-lg px-4 py-2 ${ msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/50 border border-border/40" }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center mr-2">
                      <Send className="h-4 w-4 text-primary" />
                    </div>
                    <div className="max-w-[80%] rounded-lg px-4 py-3 bg-muted/50 border border-border/40">
                      <div className="flex space-x-2">
                        <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              {messages.length === 1 && !isLoading && (
                <div className="px-4 pb-2">
                  <p className="text-xs text-muted-foreground mb-2">Try asking:</p>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "How much did I spend on food last month?",
                      "Show me my recent expenses",
                      "Add a new expense of 500 NPR for lunch",
                      "What are my total expenses this month?"
                    ].map((question, idx) => (
                      <Button
                        key={idx}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => {
                          setInput(question);
                          setTimeout(() => handleSendMessage(), 100);
                        }}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-4 border-t flex">
                <Input
                  placeholder="Ask about your expenses..."
                  className="flex-1"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && !isLoading && handleSendMessage()}
                  disabled={isLoading}
                />
                <Button
                  className="ml-2"
                  size="icon"
                  onClick={handleSendMessage}
                  disabled={isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Button
          className="w-full h-full rounded-full shadow-lg"
          variant="default"
          onClick={() => setIsExpanded(true)}
          aria-label="Open Expense Query Assistant"
        >
          <MessageSquare className="h-6 w-6" />
        </Button>
      )}
    </div>
  );
}

interface Expense {
    id: number;
    user_id: number;
    merchant_name: string | null;
    date: string;
    amount: number | string;
    currency: string;
    category: string | null;
    is_ocr_entry: boolean;
    created_at: string;
    updated_at: string;
}

interface OCRExtractedData {
    date: string | null;
    date_confidence?: number;
    merchant_name: string | null;
    merchant_confidence?: number;
    amount: number | null;
    amount_confidence?: number;
    currency: string | null;
}

interface OCRResponse {
    expense_id: number;
    extracted_data: OCRExtractedData;
    missing_fields: string[];
    message: string;
}

const fetchExpenses = async (): Promise<Expense[]> => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('No authentication token found. Please log in again.');

    try {
        const response = await axios.get(`${API_BASE_URL}/api/expenses`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
        console.error("Error fetching expenses:", error);
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            throw new Error('Unauthorized. Please log in again.');
        }
        throw error;
    }
};

const uploadOCRDraft = async (file: File): Promise<OCRResponse> => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('Authentication token not found.');

    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post<OCRResponse>(`${API_BASE_URL}/api/expenses/ocr`, formData, {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

const updateExpense = async ({ id, data }: { id: number, data: any }): Promise<Expense> => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error('Authentication token not found.');

    const response = await axios.put<Expense>(`${API_BASE_URL}/api/expenses/${id}`, data, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
};

const ExpensesPage: React.FC = () => {
    const queryClient = useQueryClient();
    const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);
    const [isScanDialogOpen, setIsScanDialogOpen] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [isOcrMode, setIsOcrMode] = useState(false);
    const [ocrResult, setOcrResult] = useState<OCRResponse | null>(null);
    const [ocrFormData, setOcrFormData] = useState<Partial<Expense>>({});
    const [ocrError, setOcrError] = useState<string | null>(null);
    const [isLoadingOcr, setIsLoadingOcr] = useState(false);

    const { data: expenses = [], isLoading, error, isFetching } = useQuery<Expense[], Error>({
        queryKey: ['expenses'],
        queryFn: fetchExpenses,
        retry: 1,
    });

    const ocrMutation = useMutation<OCRResponse, Error, File>({
        mutationFn: uploadOCRDraft,
        onSuccess: (data) => {
            toast.success(data.message || "OCR processed. Please review and add category.");

            // Format the date properly for the HTML date input (YYYY-MM-DD)
            let formattedDate = '';
            if (data.extracted_data.date) {
                try {
                    // The backend sends dates in ISO format (YYYY-MM-DD)
                    // We need to parse it correctly to display in the date input

                    // First, log the raw date from backend for debugging
                    console.log(`Raw date from backend: ${data.extracted_data.date}`);

                    // Parse the date string - handle both ISO format and other formats
                    let dateObj;

                    // Check if it's already in YYYY-MM-DD format
                    if (/^\d{4}-\d{2}-\d{2}$/.test(data.extracted_data.date)) {
                        formattedDate = data.extracted_data.date;
                        console.log(`Date already in correct format: ${formattedDate}`);
                    } else {
                        // Add time part to ensure correct timezone handling
                        const dateStr = data.extracted_data.date + 'T00:00:00Z'; // Add Z to ensure UTC
                        dateObj = new Date(dateStr);

                        if (!isNaN(dateObj.getTime())) {
                            // Use YYYY-MM-DD format for the input
                            // Use UTC methods to avoid timezone issues
                            const year = dateObj.getUTCFullYear();
                            const month = String(dateObj.getUTCMonth() + 1).padStart(2, '0');
                            const day = String(dateObj.getUTCDate()).padStart(2, '0');
                            formattedDate = `${year}-${month}-${day}`;

                            console.log(`Parsed date from backend: ${data.extracted_data.date} -> ${formattedDate}`);
                        } else {
                            console.error(`Invalid date from backend: ${data.extracted_data.date}`);
                        }
                    }
                } catch (e) {
                    console.error("Error formatting date:", e);
                    formattedDate = '';
                }
            }

            // Set today's date as default if no date is provided
            const today = new Date();
            const todayFormatted = today.toISOString().split('T')[0]; // YYYY-MM-DD format

            // Create a modified OCR result with the properly formatted date
            const modifiedData = {
                ...data,
                extracted_data: {
                    ...data.extracted_data,
                    date: formattedDate || todayFormatted
                }
            };

            // Set the OCR result with the properly formatted date
            setOcrResult(modifiedData);
            console.log("Setting OCR result:", modifiedData);

            // Initialize with empty values - SplitViewForm will populate these one by one
            // Important: We need to set the ID so the form knows which expense to update
            setOcrFormData({
                id: data.expense_id,
                date: '',
                merchant_name: '',
                amount: '',
                currency: 'NPR',
                category: null
            });

            // Log the form data for debugging
            console.log("Initial form data set:", {
                id: data.expense_id,
                date: '',
                merchant_name: '',
                amount: '',
                currency: 'NPR',
                category: null
            });

            // For the enhanced scanning experience, we keep the scanning dialog open
            // and show the results there instead of opening a separate dialog
            setIsOcrMode(true);
            setOcrError(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onError: (error) => {
            console.error("OCR Upload Error:", error);

            // Check if this is a validation error with an expense ID
            if (axios.isAxiosError(error) &&
                error.response?.status === 422 &&
                typeof error.response.data?.detail === 'object' &&
                error.response.data.detail.expense_id) {

                // This is a special case where the expense was created but validation failed
                const detail = error.response.data.detail;
                console.log("Expense created but validation failed:", detail);

                // Show a toast notification
                toast.info(detail.message || "OCR processing completed with some issues. The expense has been saved.");

                // Refresh the expenses list to show the new expense
                queryClient.invalidateQueries({ queryKey: ['expenses'] });

                // Reset the form but keep the dialog open
                if (fileInputRef.current) fileInputRef.current.value = "";
                return;
            }

            // Handle normal errors
            const errorMsg = axios.isAxiosError(error)
                ? error.response?.data?.detail || error.message
                : error.message;

            // If errorMsg is an object, try to extract a message from it
            const displayError = typeof errorMsg === 'object'
                ? JSON.stringify(errorMsg)
                : errorMsg;

            toast.error(`OCR Failed: ${displayError}`);
            setOcrError(displayError);
            setOcrResult(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onSettled: () => {
            setIsLoadingOcr(false);
        }
    });

    const updateMutation = useMutation<Expense, Error, { id: number, data: Partial<Expense> }>({
        mutationFn: updateExpense,
        onSuccess: () => {
            toast.success("Expense saved successfully!");
            queryClient.invalidateQueries({ queryKey: ['expenses'] });
            // Reset the saving flag and close the modal
            setIsSaving(false);
            closeModalAndReset();
        },
        onError: (error) => {
            console.error("Update Expense Error:", error);
            const errorMsg = axios.isAxiosError(error)
                ? error.response?.data?.detail || error.message
                : error.message;
            toast.error(`Save failed: ${errorMsg}`);
            // Reset the saving flag on error
            setIsSaving(false);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            const token = localStorage.getItem('accessToken');
            if (!token) throw new Error('Authentication token not found.');

            await axios.delete(`${API_BASE_URL}/api/expenses/${id}`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            return id;
        },
        onSuccess: (id) => {
            toast.success("Expense deleted successfully!");
            queryClient.invalidateQueries({ queryKey: ['expenses'] });
        },
        onError: (error) => {
            console.error("Delete Expense Error:", error);
            const errorMsg = axios.isAxiosError(error)
                ? error.response?.data?.detail || error.message
                : error.message;
            toast.error(`Delete failed: ${errorMsg}`);
        },
    });

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setIsLoadingOcr(true);
            setOcrError(null);
            setOcrResult(null);
            if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
                 toast.error("Invalid file type. Please use JPG, PNG, or WEBP.");
                 setIsLoadingOcr(false);
                 if (fileInputRef.current) fileInputRef.current.value = "";
                 return;
             }
            if (file.size > 5 * 1024 * 1024) {
                 toast.error("File size exceeds 5MB limit.");
                 setIsLoadingOcr(false);
                 if (fileInputRef.current) fileInputRef.current.value = "";
                 return;
             }
            ocrMutation.mutate(file);
        }
    };

    const triggerFileInput = () => {
        fileInputRef.current?.click();
    };

    const handleOcrFormChange = (field: keyof Partial<Expense>, value: any) => {
        console.log(`Updating form field: ${field} with value:`, value);
        setOcrFormData(produce((draft: Partial<Expense>) => {
            (draft as any)[field] = value;
        }));
    };

    // Add a state to track if we're saving the expense
    const [isSaving, setIsSaving] = useState(false);

    const handleSaveOcrExpense = () => {
        if (!ocrResult?.expense_id) {
            toast.error("Error: Missing OCR result or expense ID.");
            return;
        }
        if (!ocrFormData.category) {
            toast.error("Please select a category.");
            return;
        }

        const amountStr = String(ocrFormData.amount).trim();
        const amountNum = parseFloat(amountStr);
        if (isNaN(amountNum) || amountNum <= 0) {
            toast.error("Amount must be a positive number.");
            return;
        }

        let formattedDate: string | null = null;
        const dateInput = ocrFormData.date;

        if (typeof dateInput === 'string' && dateInput.length > 0) {
            if (/^\d{4}-\d{2}-\d{2}$/.test(dateInput)) {
                formattedDate = dateInput;
            } else {
                const parts = dateInput.split('/');
                if (parts.length === 3) {
                    const [month, day, year] = parts;
                    if (year && year.length === 4 && month && day) {
                        formattedDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
                        if (!/^\d{4}-\d{2}-\d{2}$/.test(formattedDate)) {
                            formattedDate = null;
                        }
                    }
                }
            }
        } else if (dateInput instanceof Date) {
            try {
                formattedDate = dateInput.toISOString().split('T')[0];
            } catch (e) { /* ignore errors */ }
        }

        if (!formattedDate) {
            toast.error("Date is required and must be in YYYY-MM-DD or MM/DD/YYYY format.");
            return;
        }

        interface FinalUpdateData {
            merchant_name: string | null;
            date: string;
            amount: number;
            currency: string;
            category: string | null;
        }
        const finalUpdateData: FinalUpdateData = {
            merchant_name: ocrFormData.merchant_name?.trim() || null,
            date: formattedDate,
            amount: amountNum,
            currency: ocrFormData.currency || 'NPR',
            category: ocrFormData.category as string | null,
        };

        console.log("Sending update data:", finalUpdateData);

        // Set the saving flag to true to prevent confirmation dialog
        setIsSaving(true);

        // Update the expense
        updateMutation.mutate({ id: ocrResult.expense_id, data: finalUpdateData });
    };

    // Function to delete an expense by ID when closing the OCR form
    // This is a silent delete without notifications
    const deleteExpense = async (id: number) => {
        try {
            const token = localStorage.getItem('accessToken');
            if (!token) throw new Error('Authentication token not found.');

            await axios.delete(`${API_BASE_URL}/api/expenses/${id}`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            console.log(`Expense ${id} deleted successfully`);
        } catch (error) {
            console.error(`Failed to delete expense ${id}:`, error);
            // We don't show an error toast here to avoid confusing the user
            // when they close the form
        }
    };

    const closeModalAndReset = () => {
        // If we have an OCR result with an expense ID and we're in OCR mode,
        // confirm with the user before discarding
        if (isOcrMode && ocrResult?.expense_id && !isSaving) {
            // Only show confirmation if we're in OCR mode with data and not saving
            const hasUserEnteredData =
                ocrFormData.category ||
                (ocrFormData.merchant_name && ocrFormData.merchant_name !== ocrResult.extracted_data.merchant_name) ||
                (ocrFormData.amount && ocrFormData.amount !== ocrResult.extracted_data.amount);

            if (hasUserEnteredData) {
                const confirmClose = window.confirm(
                    "Are you sure you want to close? Your scanned expense will be discarded."
                );
                if (!confirmClose) {
                    return; // User canceled, don't close
                }
            }

            // Delete the expense from the database if we're not saving
            if (!isSaving) {
                deleteExpense(ocrResult.expense_id);
            }
        }

        setIsAddExpenseOpen(false);
        setIsScanDialogOpen(false); // Also close the scanning dialog
        setIsOcrMode(false);
        setOcrResult(null);
        setOcrFormData({});
        setOcrError(null);
        setIsSaving(false); // Reset the saving flag
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const handleManualAddSuccess = () => {
        closeModalAndReset();
        queryClient.invalidateQueries({ queryKey: ['expenses'] });
    };

    const handleDeleteExpense = (id: number) => {
        if (window.confirm("Are you sure you want to delete this expense? This action cannot be undone.")) {
            deleteMutation.mutate(id);
        }
    };

  return (
        <div className="space-y-6 container mx-auto py-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-right tracking-tight">Expenses</h1>
                    <p className="text-muted-foreground">Manage and view your expenses</p>
                </div>
                <div className="flex gap-2">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        accept="image/jpeg, image/png, image/webp"
                        style={{ display: 'none' }}
                        disabled={isLoadingOcr}
                    />
                    <Button onClick={() => setIsScanDialogOpen(true)} disabled={isLoadingOcr || isFetching}>
                        <ScanLine className="mr-2 h-4 w-4" />
                        {isLoadingOcr ? "Processing..." : "Scan Receipt"}
                    </Button>
                    <Dialog
                        open={isAddExpenseOpen}
                        onOpenChange={(isOpen) => {
                        if (!isOpen) {
                            // Don't close if we're in the process of saving
                            if (isSaving) {
                                return;
                            }
                            // When dialog is closing, handle it properly
                            closeModalAndReset();
                        } else {
                            setIsAddExpenseOpen(true);
                        }
                    }}>
      <DialogTrigger asChild>
                            <Button onClick={() => { setIsOcrMode(false); setOcrResult(null); setOcrFormData({}); }} disabled={isFetching || isLoadingOcr}>
          <Plus className="mr-2 h-4 w-4" />
                                Add Manually
        </Button>
      </DialogTrigger>
                        <DialogContent className="sm:max-w-[425px]" onEscapeKeyDown={(e) => {
                            // Prevent default to stop automatic closing
                            e.preventDefault();

                            // Don't show confirmation if we're in the process of saving
                            if (isSaving) {
                                return;
                            }

                            // Only close if user confirms
                            if (isOcrMode && ocrResult?.expense_id) {
                                const confirmClose = window.confirm(
                                    "Are you sure you want to close? Your scanned expense will be discarded."
                                );
                                if (confirmClose) {
                                    closeModalAndReset();
                                }
                            } else {
                                closeModalAndReset();
                            }
                        }} onInteractOutside={(e) => {
                            // Prevent default to stop automatic closing
                            e.preventDefault();

                            // Don't show confirmation if we're in the process of saving
                            if (isSaving) {
                                return;
                            }

                            // Only close if user confirms
                            if (isOcrMode && ocrResult?.expense_id) {
                                const confirmClose = window.confirm(
                                    "Are you sure you want to close? Your scanned expense will be discarded."
                                );
                                if (confirmClose) {
                                    closeModalAndReset();
                                }
                            } else {
                                closeModalAndReset();
                            }
                        }}>
                            {isOcrMode && ocrResult ? (
                                <>
            <DialogHeader>
                                        <DialogTitle>Review Scanned Expense</DialogTitle>
              <DialogDescription>
                                            {ocrResult.message} Verify the extracted details and select a category.
              </DialogDescription>
            </DialogHeader>
                                    {ocrError && <p className="text-sm text-red-500">Error: {ocrError}</p>}
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                                            <Label htmlFor="ocr-merchant" className="text-right">Merchant</Label>
                                            <Input id="ocr-merchant" value={ocrFormData.merchant_name || ''} onChange={e => handleOcrFormChange('merchant_name', e.target.value)} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                                            <Label htmlFor="ocr-date" className="text-right">Date*</Label>
                                            <Input id="ocr-date" type="date" value={ocrFormData.date || ''} onChange={e => handleOcrFormChange('date', e.target.value)} className="col-span-3" required />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                                            <Label htmlFor="ocr-amount" className="text-right">Amount*</Label>
                                            <Input id="ocr-amount" type="number" step="0.01" value={ocrFormData.amount || ''} onChange={e => handleOcrFormChange('amount', e.target.value ? parseFloat(e.target.value) : null)} className="col-span-3" required />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                                            <Label htmlFor="ocr-category" className="text-right">Category*</Label>
                                            <Select
                                                value={ocrFormData.category || undefined}
                                                onValueChange={(value) => handleOcrFormChange('category', value)}
                                                required
                                            >
                  <SelectTrigger className="col-span-3">
                                                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                                                    {["Food", "Travel", "Entertainment", "Household Bill", "Other"].map(cat => (
                                                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                                                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
                                    <div className="flex gap-2 mt-4">
                                        <Button
                                            onClick={closeModalAndReset}
                                            variant="outline"
                                            type="button"
                                            className="flex-1"
                                            disabled={updateMutation.isPending}
                                        >
                                            Cancel
                                        </Button>
                                        <Button
                                            onClick={handleSaveOcrExpense}
                                            disabled={updateMutation.isPending}
                                            className="flex-1"
                                        >
                                            {updateMutation.isPending ? "Saving..." : "Save Expense"}
                                        </Button>
                                    </div>
                                </>
                            ) : (
                                <>
            <DialogHeader>
                                        <DialogTitle>Add Manual Expense</DialogTitle>
              <DialogDescription>
                                            Fill in the details for your new expense.
              </DialogDescription>
            </DialogHeader>
                                    <AddExpenseForm
                                        onSuccess={handleManualAddSuccess}
                                        onCancel={closeModalAndReset}
                                    />
                                </>
                            )}
                        </DialogContent>
                    </Dialog>
              </div>
            </div>

            {/* Enhanced Scanning Dialog */}
            <ScanningDialog
                open={isScanDialogOpen}
                onOpenChange={(isOpen) => {
                    if (!isOpen && !isLoadingOcr) {
                        setIsScanDialogOpen(false);
                    }
                }}
                onFileAccepted={(file) => {
                    setIsLoadingOcr(true);
                    setOcrError(null);
                    setOcrResult(null);
                    ocrMutation.mutate(file);
                }}
                isLoadingOcr={isLoadingOcr}
                ocrResult={ocrResult}
                ocrError={ocrError}
                ocrFormData={ocrFormData}
                onOcrFormChange={handleOcrFormChange}
                onSaveOcrExpense={handleSaveOcrExpense}
                onCancel={closeModalAndReset}
                isSaving={isSaving}
            />

            <div className="border rounded-lg overflow-hidden">
                {isLoading && <p className="p-4 text-center">Loading expenses...</p>}
                {!isLoading && error && <p className="p-4 text-red-500 text-center">Error fetching expenses: {error.message}</p>}

                {!error && (
                    <Table>
                        <TableCaption className="py-4">
                            {isLoading ? "Loading..." :
                             expenses.length === 0
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
                                <TableHead className="w-[80px]">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {!isLoading && expenses.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="h-24 text-center">
                                        No expenses found.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                expenses.map((exp) => {
                                    const numericAmount = parseFloat(exp.amount as string);
                                    const displayAmount = !isNaN(numericAmount)
                                        ? numericAmount.toFixed(2)
                                        : 'N/A';

  return (
                                        <TableRow key={exp.id}>
                                            <TableCell>{exp.date ? format(new Date(exp.date), 'PPP') : 'N/A'}</TableCell>
                                            <TableCell className="font-medium">{exp.merchant_name || 'N/A'}</TableCell>
                                            <TableCell>{exp.category || 'N/A'}</TableCell>
                                            <TableCell className="text-right">
                                                {exp.currency} {displayAmount}
                                            </TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleDeleteExpense(exp.id)}
                                                    title="Delete expense"
                                                    className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-100"
                                                    disabled={deleteMutation.isPending}
                                                >
                                                    <Trash className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    );
                                })
                            )}
                        </TableBody>
                    </Table>
        )}
      </div>

      <ExpenseQueryChatbot />
    </div>
  );
};

export default ExpensesPage;
