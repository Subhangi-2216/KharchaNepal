import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CalendarDays, 
  Check, 
  Loader2, 
  DollarSign,
  Building,
  Calendar,
  Eye,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { format } from 'date-fns';

interface TransactionApproval {
  id: number;
  user_id: number;
  email_message_id: number;
  extracted_data: {
    amounts?: string[];
    dates?: string[];
    merchants?: string[];
    transaction_ids?: string[];
    source: string;
  };
  confidence_score: number;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  created_at: string;
  email_message?: {
    subject: string;
    sender: string;
    received_at: string;
  };
}

interface TransactionFormData {
  merchant_name: string;
  amount: number | string;
  date: string;
  category: string;
  currency: string;
}

interface TransactionDetailFormProps {
  approval: TransactionApproval;
  formData: TransactionFormData;
  onFormChange: (field: keyof TransactionFormData, value: any) => void;
  onApprove: () => void;
  onReject: () => void;
  isProcessing: boolean;
}

const categories = [
  "Food",
  "Travel", 
  "Entertainment",
  "Household Bill",
  "Other"
] as const;

const currencies = [
  "NPR",
  "USD",
  "EUR",
  "INR"
] as const;

export function TransactionDetailForm({
  approval,
  formData,
  onFormChange,
  onApprove,
  onReject,
  isProcessing
}: TransactionDetailFormProps) {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    formData.date ? new Date(formData.date) : undefined
  );

  // Handle date selection
  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    if (date) {
      onFormChange('date', format(date, 'yyyy-MM-dd'));
    } else {
      onFormChange('date', '');
    }
  };

  // Handle selecting from extracted values
  const handleSelectExtractedValue = (field: keyof TransactionFormData, value: string) => {
    onFormChange(field, value);
  };

  // Validate form
  const isFormValid = () => {
    return formData.merchant_name && 
           formData.amount && 
           formData.date && 
           formData.category;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Left side - Extracted Data */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium mb-2">Extracted Data</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Click on any value below to use it in the form
          </p>
        </div>

        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {/* Extracted Amounts */}
            {approval.extracted_data.amounts && approval.extracted_data.amounts.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Detected Amounts</span>
                </div>
                <div className="space-y-1">
                  {approval.extracted_data.amounts.map((amount, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      size="sm"
                      className="justify-start h-auto p-2 text-left"
                      onClick={() => handleSelectExtractedValue('amount', amount)}
                    >
                      <span className="text-sm">{amount}</span>
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Dates */}
            {approval.extracted_data.dates && approval.extracted_data.dates.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">Detected Dates</span>
                </div>
                <div className="space-y-1">
                  {approval.extracted_data.dates.map((date, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      size="sm"
                      className="justify-start h-auto p-2 text-left"
                      onClick={() => handleSelectExtractedValue('date', date)}
                    >
                      <span className="text-sm">{date}</span>
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Merchants */}
            {approval.extracted_data.merchants && approval.extracted_data.merchants.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Building className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-medium">Detected Merchants</span>
                </div>
                <div className="space-y-1">
                  {approval.extracted_data.merchants.map((merchant, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      size="sm"
                      className="justify-start h-auto p-2 text-left"
                      onClick={() => handleSelectExtractedValue('merchant_name', merchant)}
                    >
                      <span className="text-sm">{merchant}</span>
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Transaction IDs */}
            {approval.extracted_data.transaction_ids && approval.extracted_data.transaction_ids.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Eye className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">Transaction IDs</span>
                </div>
                <div className="space-y-1">
                  {approval.extracted_data.transaction_ids.map((id, index) => (
                    <div key={index} className="text-sm text-muted-foreground font-mono p-2 bg-muted/50 rounded">
                      {id}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Right side - Form */}
      <ScrollArea className="h-[400px] pr-4">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium">Transaction Details</h3>
            <p className="text-sm text-muted-foreground">
              Review and edit the transaction information
            </p>
          </div>

          <div className="space-y-4">
            {/* Merchant Name Field */}
            <div className="space-y-2">
              <Label htmlFor="merchant_name">Merchant Name *</Label>
              <Input
                id="merchant_name"
                value={formData.merchant_name}
                onChange={(e) => onFormChange('merchant_name', e.target.value)}
                placeholder="Enter merchant name"
                className={cn(!formData.merchant_name && "border-red-200")}
              />
            </div>

            {/* Amount Field */}
            <div className="space-y-2">
              <Label htmlFor="amount">Amount *</Label>
              <div className="flex gap-2">
                <Select
                  value={formData.currency}
                  onValueChange={(value) => onFormChange('currency', value)}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {currencies.map((currency) => (
                      <SelectItem key={currency} value={currency}>
                        {currency}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => onFormChange('amount', e.target.value)}
                  placeholder="0.00"
                  className={cn(!formData.amount && "border-red-200", "flex-1")}
                />
              </div>
            </div>

            {/* Date Field */}
            <div className="space-y-2">
              <Label>Date *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !selectedDate && "text-muted-foreground",
                      !formData.date && "border-red-200"
                    )}
                  >
                    <CalendarDays className="mr-2 h-4 w-4" />
                    {selectedDate ? format(selectedDate, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <CalendarComponent
                    mode="single"
                    selected={selectedDate}
                    onSelect={handleDateSelect}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            {/* Category Field */}
            <div className="space-y-2">
              <Label>Category *</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => onFormChange('category', value)}
              >
                <SelectTrigger className={cn(!formData.category && "border-red-200")}>
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Form Validation Alert */}
          {!isFormValid() && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Please fill in all required fields before approving the transaction.
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button
              onClick={onReject}
              variant="outline"
              disabled={isProcessing}
              className="flex-1 flex items-center gap-2"
            >
              <ThumbsDown className="h-4 w-4" />
              Reject
            </Button>
            <Button
              onClick={onApprove}
              disabled={isProcessing || !isFormValid()}
              className="flex-1 flex items-center gap-2"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ThumbsUp className="h-4 w-4" />
              )}
              Approve & Add to Expenses
            </Button>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

export default TransactionDetailForm;
