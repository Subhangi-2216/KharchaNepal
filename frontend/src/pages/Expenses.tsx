import React, { useState, useRef, ChangeEvent } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { format } from 'date-fns';
import { produce } from 'immer';

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import AddExpenseForm from '@/components/expenses/AddExpenseForm';
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ExpenseQueryChatbot() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { role: "system", content: "Hello! I'm your Expense Query Assistant. Ask me about your expenses or tell me to add a new one." }
  ]);
  const [input, setInput] = useState("");

  const handleSendMessage = () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: "user" as const, content: input }];
    setMessages(newMessages);
    
    setTimeout(() => {
      let botResponse = "I'm not sure how to answer that query yet.";
      if (input.toLowerCase().includes("how much") && input.toLowerCase().includes("food")) {
        botResponse = "Based on current data, you seem to have spent X on Food this month (Note: Real-time query needed).";
      } else if (input.toLowerCase().includes("add") && input.toLowerCase().includes("expense")) {
        botResponse = "To add an expense, please use the 'Add New Expense' button.";
      }
      setMessages(prev => [...prev, { role: "system" as const, content: botResponse }]);
    }, 500);
    
    setInput("");
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
                    <div className={`max-w-[80%] rounded-lg px-4 py-2 ${ msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted" }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t flex">
                <Input 
                  placeholder="Ask about your expenses..." 
                  className="flex-1" 
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSendMessage()}
                />
                <Button 
                  className="ml-2" 
                  size="icon"
                  onClick={handleSendMessage}
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
    merchant_name: string | null;
    amount: number | null;
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
            setOcrResult(data); 
            setOcrFormData({
                id: data.expense_id,
                date: data.extracted_data.date ?? '',
                merchant_name: data.extracted_data.merchant_name ?? '',
                amount: data.extracted_data.amount ?? '',
                currency: data.extracted_data.currency ?? 'NPR',
                category: null
            });
            setIsOcrMode(true);
            setIsAddExpenseOpen(true);
            setOcrError(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onError: (error) => {
            console.error("OCR Upload Error:", error);
            const errorMsg = axios.isAxiosError(error) 
                ? error.response?.data?.detail || error.message 
                : error.message;
            toast.error(`OCR Failed: ${errorMsg}`);
            setOcrError(errorMsg);
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
            closeModalAndReset();
        },
        onError: (error) => {
            console.error("Update Expense Error:", error);
            const errorMsg = axios.isAxiosError(error) 
                ? error.response?.data?.detail || error.message 
                : error.message;
            toast.error(`Save failed: ${errorMsg}`);
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
        setOcrFormData(produce((draft: Partial<Expense>) => {
            (draft as any)[field] = value;
        }));
    };
     
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
        updateMutation.mutate({ id: ocrResult.expense_id, data: finalUpdateData });
    };

    const closeModalAndReset = () => {
        setIsAddExpenseOpen(false);
        setIsOcrMode(false);
        setOcrResult(null);
        setOcrFormData({});
        setOcrError(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const handleManualAddSuccess = () => {
        closeModalAndReset();
        queryClient.invalidateQueries({ queryKey: ['expenses'] });
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
                    <Button onClick={triggerFileInput} disabled={isLoadingOcr || isFetching}>
                        <ScanLine className="mr-2 h-4 w-4" />
                        {isLoadingOcr ? "Processing..." : "Scan Receipt"}
                    </Button>
                    <Dialog open={isAddExpenseOpen} onOpenChange={(isOpen) => { if (!isOpen) closeModalAndReset(); else setIsAddExpenseOpen(true); }}>
      <DialogTrigger asChild>
                            <Button onClick={() => { setIsOcrMode(false); setOcrResult(null); setOcrFormData({}); }} disabled={isFetching || isLoadingOcr}> 
          <Plus className="mr-2 h-4 w-4" />
                                Add Manually
        </Button>
      </DialogTrigger>
                        <DialogContent className="sm:max-w-[425px]">
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
                                    <Button 
                                        onClick={handleSaveOcrExpense} 
                                        disabled={updateMutation.isPending}
                                        className="w-full mt-4"
                                    >
                                        {updateMutation.isPending ? "Saving..." : "Save Expense"}
                                    </Button>
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
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {!isLoading && expenses.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="h-24 text-center">
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
