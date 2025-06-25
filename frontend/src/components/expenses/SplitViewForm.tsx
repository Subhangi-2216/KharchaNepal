import React, { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CalendarDays, Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import ScanningAnimation from './ScanningAnimation';

interface Expense {
  id?: number;
  user_id?: number;
  merchant_name?: string | null;
  date?: string;
  amount?: number | string;
  currency?: string;
  category?: string | null;
  is_ocr_entry?: boolean;
  created_at?: string;
  updated_at?: string;
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

interface SplitViewFormProps {
  imageUrl: string;
  ocrResult: OCRResponse | null;
  isScanning: boolean;
  onSave: (data: Partial<Expense>) => void;
  onCancel: () => void;
  formData: Partial<Expense>;
  onFormChange: (field: keyof Partial<Expense>, value: any) => void;
  isSaving: boolean;
}

const SplitViewForm: React.FC<SplitViewFormProps> = ({
  imageUrl,
  ocrResult,
  isScanning,
  onSave,
  onCancel,
  formData,
  onFormChange,
  isSaving
}) => {
  const [activeField, setActiveField] = useState<keyof Partial<Expense> | null>(null);
  const [scanComplete, setScanComplete] = useState(false);
  const [fieldStatus, setFieldStatus] = useState<Record<string, 'pending' | 'scanning' | 'complete'>>({
    merchant_name: 'pending',
    date: 'pending',
    amount: 'pending',
    category: 'pending'
  });
  // Add a ref to track the last processed OCR result ID to prevent duplicate animations
  const lastProcessedOcrId = React.useRef<number | null>(null);

  // Simpler approach to field population

  // Reset fields when scanning starts
  useEffect(() => {
    if (isScanning) {
      console.log("Scanning started, resetting fields");
      setFieldStatus({
        merchant_name: 'pending',
        date: 'pending',
        amount: 'pending',
        category: 'pending'
      });

      // Reset the lastProcessedOcrId to allow new animations
      lastProcessedOcrId.current = null;

      // Reset form data in parent component
      onFormChange('merchant_name', '');
      onFormChange('date', '');
      onFormChange('amount', '');
    }
  }, [isScanning, onFormChange]);

  // This effect runs when the scanning is complete
  useEffect(() => {
    if (scanComplete && ocrResult) {
      console.log("Scan complete, will start populating fields");
    }
  }, [scanComplete, ocrResult]);

  // This effect handles the sequential field population
  useEffect(() => {
    // Only run when we have OCR results and scanning is not in progress
    // Also check if we've already processed this OCR result to prevent duplicate animations
    if (!isScanning && ocrResult && lastProcessedOcrId.current !== ocrResult.expense_id) {
      console.log("Starting field population with OCR data:", ocrResult);

      // Store the current OCR result ID to prevent duplicate animations
      lastProcessedOcrId.current = ocrResult.expense_id;

      // Extract the data from OCR result
      const extractedData = {
        merchant_name: ocrResult.extracted_data.merchant_name || '',
        date: ocrResult.extracted_data.date || '',
        amount: ocrResult.extracted_data.amount || '',
        currency: ocrResult.extracted_data.currency || 'NPR'
      };

      console.log("Extracted data for population:", extractedData);

      // Define the sequence function
      const populateFields = async () => {
        // Merchant name
        console.log("Populating merchant name field");
        setFieldStatus(prev => ({ ...prev, merchant_name: 'scanning' }));
        setActiveField('merchant_name');
        await new Promise(resolve => setTimeout(resolve, 800));
        console.log("Setting merchant name:", extractedData.merchant_name);
        onFormChange('merchant_name', extractedData.merchant_name);
        setFieldStatus(prev => ({ ...prev, merchant_name: 'complete' }));

        // Small delay before next field
        await new Promise(resolve => setTimeout(resolve, 600));

        // Date
        console.log("Populating date field");
        setFieldStatus(prev => ({ ...prev, date: 'scanning' }));
        setActiveField('date');
        await new Promise(resolve => setTimeout(resolve, 800));
        console.log("Setting date:", extractedData.date);
        onFormChange('date', extractedData.date);
        setFieldStatus(prev => ({ ...prev, date: 'complete' }));

        // Small delay before next field
        await new Promise(resolve => setTimeout(resolve, 600));

        // Amount
        console.log("Populating amount field");
        setFieldStatus(prev => ({ ...prev, amount: 'scanning' }));
        setActiveField('amount');
        await new Promise(resolve => setTimeout(resolve, 800));
        console.log("Setting amount:", extractedData.amount);
        onFormChange('amount', extractedData.amount);

        // Update currency if available
        if (extractedData.currency) {
          onFormChange('currency', extractedData.currency);
        }

        setFieldStatus(prev => ({ ...prev, amount: 'complete' }));

        // Animation complete
        console.log("Field population complete");
        setActiveField(null);
      };

      // Start the sequence after a delay to ensure scanning animation is complete
      const timer = setTimeout(() => {
        populateFields();
      }, 500);

      // Clean up the timer if component unmounts
      return () => clearTimeout(timer);
    }
  }, [isScanning, ocrResult, onFormChange]);

  // This function is called when the scanning animation completes
  const handleScanComplete = () => {
    console.log("Scan animation complete, triggering field population");
    // Reset the lastProcessedOcrId to allow the animation to run
    lastProcessedOcrId.current = null;
    // Force a re-render to ensure the field population effect runs
    setScanComplete(true);
  };

  const getFieldIcon = (field: string) => {
    if (fieldStatus[field] === 'scanning') {
      return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
    } else if (fieldStatus[field] === 'complete') {
      return <Check className="h-4 w-4 text-green-500" />;
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
      {/* Left side - Image preview with scanning animation */}
      <div className="relative rounded-md border overflow-hidden bg-muted/20 flex items-center justify-center h-[400px] md:h-full">
        {imageUrl && (
          <img
            src={imageUrl}
            alt="Receipt"
            className="max-w-full max-h-full object-contain"
          />
        )}
        <ScanningAnimation
          isScanning={isScanning}
          onScanComplete={handleScanComplete}
          className="absolute inset-0"
        />
      </div>

      {/* Right side - Form */}
      <ScrollArea className="h-[400px] md:h-full p-1">
        <div className="space-y-6 p-2">
          <div>
            <h3 className="text-lg font-medium">Receipt Details</h3>
            <p className="text-sm text-muted-foreground">
              {isScanning
                ? "Scanning receipt..."
                : scanComplete
                  ? "Review the extracted information below"
                  : "Upload a receipt to begin scanning"}
            </p>
          </div>

          <div className="space-y-4">
            {/* Merchant Name Field */}
            <div
              className={cn(
                "space-y-2 rounded-md p-3 transition-all duration-300",
                activeField === 'merchant_name' && "bg-primary/5 border border-primary/20",
                fieldStatus.merchant_name === 'pending' && "opacity-70 translate-y-1"
              )}
            >
              <div className="flex items-center justify-between">
                <Label htmlFor="merchant_name" className="text-sm font-medium">
                  Merchant Name
                </Label>
                {getFieldIcon('merchant_name')}
              </div>
              <Input
                id="merchant_name"
                value={formData.merchant_name || ''}
                onChange={(e) => {
                  console.log("Merchant name changed:", e.target.value);
                  onFormChange('merchant_name', e.target.value);
                }}
                placeholder="Merchant name"
                className={cn(
                  fieldStatus.merchant_name === 'scanning' && "opacity-50"
                )}
                disabled={fieldStatus.merchant_name === 'scanning'}
              />
              {ocrResult?.extracted_data.merchant_confidence !== undefined && (
                <p className="text-xs text-muted-foreground">
                  Confidence: {Math.round(ocrResult.extracted_data.merchant_confidence * 100)}%
                </p>
              )}
            </div>

            {/* Date Field */}
            <div
              className={cn(
                "space-y-2 rounded-md p-3 transition-all duration-300",
                activeField === 'date' && "bg-primary/5 border border-primary/20",
                fieldStatus.date === 'pending' && "opacity-70 translate-y-1"
              )}
            >
              <div className="flex items-center justify-between">
                <Label htmlFor="date" className="text-sm font-medium">
                  Date
                </Label>
                {getFieldIcon('date')}
              </div>
              <div className="relative">
                <Input
                  id="date"
                  type="date"
                  value={formData.date || ''}
                  onChange={(e) => onFormChange('date', e.target.value)}
                  className={cn(
                    fieldStatus.date === 'scanning' && "opacity-50"
                  )}
                  disabled={fieldStatus.date === 'scanning'}
                />
                <CalendarDays className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
              </div>
              {ocrResult?.extracted_data.date_confidence !== undefined && (
                <p className="text-xs text-muted-foreground">
                  Confidence: {Math.round(ocrResult.extracted_data.date_confidence * 100)}%
                </p>
              )}
            </div>

            {/* Amount Field */}
            <div
              className={cn(
                "space-y-2 rounded-md p-3 transition-all duration-300",
                activeField === 'amount' && "bg-primary/5 border border-primary/20",
                fieldStatus.amount === 'pending' && "opacity-70 translate-y-1"
              )}
            >
              <div className="flex items-center justify-between">
                <Label htmlFor="amount" className="text-sm font-medium">
                  Amount
                </Label>
                {getFieldIcon('amount')}
              </div>
              <div className="relative">
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  value={formData.amount || ''}
                  onChange={(e) => onFormChange('amount', e.target.value ? parseFloat(e.target.value) : '')}
                  placeholder="0.00"
                  className={cn(
                    fieldStatus.amount === 'scanning' && "opacity-50"
                  )}
                  disabled={fieldStatus.amount === 'scanning'}
                />
                <div className="absolute inset-y-0 right-0 flex items-center">
                  <Select
                    value={formData.currency || 'NPR'}
                    onValueChange={(value) => onFormChange('currency', value)}
                    disabled={false} // Always enable editing
                  >
                    <SelectTrigger className="h-8 w-[70px] border-0 bg-transparent">
                      <SelectValue placeholder="NPR" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="NPR">NPR</SelectItem>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="INR">INR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {ocrResult?.extracted_data.amount_confidence !== undefined && (
                <p className="text-xs text-muted-foreground">
                  Confidence: {Math.round(ocrResult.extracted_data.amount_confidence * 100)}%
                </p>
              )}
            </div>

            {/* Category Field */}
            <div
              className={cn(
                "space-y-2 rounded-md p-3 transition-all duration-300",
                activeField === 'category' && "bg-primary/5 border border-primary/20",
                fieldStatus.category === 'pending' && "opacity-70 translate-y-1"
              )}
            >
              <div className="flex items-center justify-between">
                <Label htmlFor="category" className="text-sm font-medium">
                  Category
                </Label>
                {getFieldIcon('category')}
              </div>
              <Select
                value={formData.category || ""}
                onValueChange={(value) => {
                  console.log("Category selected:", value);
                  onFormChange('category', value);
                }}
                disabled={false} // Always enable editing
              >
                <SelectTrigger className={cn(
                  fieldStatus.category === 'scanning' && "opacity-50"
                )}>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Food">Food</SelectItem>
                  <SelectItem value="Travel">Travel</SelectItem>
                  <SelectItem value="Entertainment">Entertainment</SelectItem>
                  <SelectItem value="Household Bill">Household Bill</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={onCancel}
              variant="outline"
              type="button"
              className="flex-1"
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                console.log("Save button clicked, formData:", formData);
                console.log("Save button state:", {
                  isSaving,
                  isScanning,
                  scanComplete,
                  hasName: !!formData.merchant_name,
                  hasDate: !!formData.date,
                  hasAmount: !!formData.amount,
                  hasCategory: !!formData.category
                });
                onSave(formData);
              }}
              disabled={
                isSaving ||
                isScanning ||
                !formData.merchant_name ||
                !formData.date ||
                !formData.amount ||
                !formData.category
              }
              className="flex-1"
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Expense"
              )}
            </Button>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};

export default SplitViewForm;
