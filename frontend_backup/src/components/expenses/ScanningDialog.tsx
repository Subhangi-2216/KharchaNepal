import React, { useState, useRef, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScanLine, Upload } from 'lucide-react';
import DropzoneArea from './DropzoneArea';
import SplitViewForm from './SplitViewForm';
import { toast } from 'sonner';

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

interface ScanningDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onFileAccepted: (file: File) => void;
  isLoadingOcr: boolean;
  ocrResult: OCRResponse | null;
  ocrError: string | null;
  ocrFormData: Partial<Expense>;
  onOcrFormChange: (field: keyof Partial<Expense>, value: any) => void;
  onSaveOcrExpense: () => void;
  onCancel: () => void;
  isSaving: boolean;
}

const ScanningDialog: React.FC<ScanningDialogProps> = ({
  open,
  onOpenChange,
  onFileAccepted,
  isLoadingOcr,
  ocrResult,
  ocrError,
  ocrFormData,
  onOcrFormChange,
  onSaveOcrExpense,
  onCancel,
  isSaving
}) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isUploadView, setIsUploadView] = useState(true);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setIsUploadView(true);
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
        setImageUrl(null);
      }
      setUploadedFile(null);
    }
  }, [open]);

  // Handle file upload
  const handleFileAccepted = (file: File) => {
    setUploadedFile(file);

    // Create preview URL
    const objectUrl = URL.createObjectURL(file);
    setImageUrl(objectUrl);

    // Switch to scanning view
    setIsUploadView(false);

    // Pass file to parent for OCR processing
    onFileAccepted(file);
  };

  // Handle new scan button
  const handleNewScan = () => {
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }
    setImageUrl(null);
    setUploadedFile(null);
    setIsUploadView(true);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      // Don't close if we're in the process of scanning or saving
      if (!isOpen && (isLoadingOcr || isSaving)) {
        return;
      }
      onOpenChange(isOpen);
    }}>
      <DialogContent
        className={isUploadView ? "sm:max-w-md" : "sm:max-w-4xl"}
        onEscapeKeyDown={(e) => {
          // Prevent default to stop automatic closing
          e.preventDefault();

          // Don't close if we're in the process of scanning or saving
          if (isLoadingOcr || isSaving) {
            return;
          }

          // Only close if user confirms when we have data and fields are filled
          if (!isUploadView && ocrResult?.expense_id) {
            // Check if we have all required fields filled
            const hasAllRequiredFields =
              ocrFormData.merchant_name &&
              ocrFormData.date &&
              ocrFormData.amount &&
              ocrFormData.category;

            if (hasAllRequiredFields) {
              // If all fields are filled, ask if they want to save
              const confirmSave = window.confirm(
                "Do you want to save this expense before closing?"
              );
              if (confirmSave) {
                onSaveOcrExpense();
                return;
              }
            }

            // If not all fields are filled or user doesn't want to save
            const confirmClose = window.confirm(
              "Are you sure you want to close? Your scanned expense will be discarded."
            );
            if (confirmClose) {
              onCancel();
            }
          } else {
            onCancel();
          }
        }}
        onInteractOutside={(e) => {
          // Prevent default to stop automatic closing
          e.preventDefault();

          // Don't close if we're in the process of scanning or saving
          if (isLoadingOcr || isSaving) {
            return;
          }

          // Only close if user confirms when we have data and fields are filled
          if (!isUploadView && ocrResult?.expense_id) {
            // Check if we have all required fields filled
            const hasAllRequiredFields =
              ocrFormData.merchant_name &&
              ocrFormData.date &&
              ocrFormData.amount &&
              ocrFormData.category;

            if (hasAllRequiredFields) {
              // If all fields are filled, ask if they want to save
              const confirmSave = window.confirm(
                "Do you want to save this expense before closing?"
              );
              if (confirmSave) {
                onSaveOcrExpense();
                return;
              }
            }

            // If not all fields are filled or user doesn't want to save
            const confirmClose = window.confirm(
              "Are you sure you want to close? Your scanned expense will be discarded."
            );
            if (confirmClose) {
              onCancel();
            }
          } else {
            onCancel();
          }
        }}>
        {isUploadView ? (
          <>
            <DialogHeader>
              <DialogTitle>Scan Receipt</DialogTitle>
              <DialogDescription>
                Drag and drop a receipt image or click to browse. The system will automatically extract expense details using OCR.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <DropzoneArea
                onFileAccepted={handleFileAccepted}
                isLoading={isLoadingOcr}
                maxSize={5 * 1024 * 1024} // 5MB
                acceptedFileTypes={['image/jpeg', 'image/png', 'image/webp']}
                className="w-full"
              />
            </div>
            {ocrError && (
              <div className="text-sm text-red-500 mt-2">
                Error: {ocrError}
              </div>
            )}
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Scanning Receipt</DialogTitle>
              <DialogDescription>
                {isLoadingOcr
                  ? "Processing your receipt with OCR technology..."
                  : "Review the extracted information and make any necessary corrections."}
              </DialogDescription>
            </DialogHeader>

            <div className="mt-4">
              {/* Log OCR result for debugging */}
              {ocrResult ? (
                <>{console.log("ScanningDialog passing OCR result to SplitViewForm:", ocrResult)}</>
              ) : null}

              <SplitViewForm
                imageUrl={imageUrl || ''}
                ocrResult={ocrResult}
                isScanning={isLoadingOcr}
                onSave={onSaveOcrExpense}
                onCancel={onCancel}
                formData={ocrFormData}
                onFormChange={onOcrFormChange}
                isSaving={isSaving}
              />
            </div>

            {!isLoadingOcr && (
              <div className="mt-4 flex justify-start">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNewScan}
                  disabled={isSaving}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Scan New Receipt
                </Button>
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ScanningDialog;
