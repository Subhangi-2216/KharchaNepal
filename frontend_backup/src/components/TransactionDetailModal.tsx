import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Mail, 
  AlertTriangle, 
  X,
  Calendar,
  Building,
  DollarSign,
  Eye
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import TransactionDetailForm from './TransactionDetailForm';

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

interface TransactionDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  approval: TransactionApproval | null;
  onApprove: (approvalId: number, editedData?: TransactionFormData) => Promise<void>;
  onReject: (approvalId: number) => Promise<void>;
  isProcessing: boolean;
}

export function TransactionDetailModal({
  open,
  onOpenChange,
  approval,
  onApprove,
  onReject,
  isProcessing
}: TransactionDetailModalProps) {
  const [formData, setFormData] = useState<TransactionFormData>({
    merchant_name: '',
    amount: '',
    date: '',
    category: '',
    currency: 'NPR'
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const { toast } = useToast();

  // Initialize form data when approval changes
  useEffect(() => {
    if (approval) {
      // Extract the most likely values from the arrays
      const primaryAmount = approval.extracted_data.amounts?.[0] || '';
      const primaryDate = approval.extracted_data.dates?.[0] || '';
      const primaryMerchant = approval.extracted_data.merchants?.[0] || '';

      setFormData({
        merchant_name: primaryMerchant,
        amount: primaryAmount,
        date: primaryDate,
        category: '',
        currency: 'NPR'
      });
      setHasUnsavedChanges(false);
    }
  }, [approval]);

  // Handle form field changes
  const handleFormChange = (field: keyof TransactionFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setHasUnsavedChanges(true);
  };

  // Handle modal close with unsaved changes warning
  const handleClose = () => {
    if (hasUnsavedChanges) {
      const confirmClose = window.confirm(
        "You have unsaved changes. Are you sure you want to close without saving?"
      );
      if (!confirmClose) return;
    }
    onOpenChange(false);
    setHasUnsavedChanges(false);
  };

  // Handle approve with edited data
  const handleApprove = async () => {
    if (!approval) return;

    try {
      await onApprove(approval.id, formData);
      setHasUnsavedChanges(false);
      onOpenChange(false);
    } catch (error) {
      console.error('Error approving transaction:', error);
    }
  };

  // Handle reject
  const handleReject = async () => {
    if (!approval) return;

    try {
      await onReject(approval.id);
      onOpenChange(false);
    } catch (error) {
      console.error('Error rejecting transaction:', error);
    }
  };

  // Get confidence badge styling
  const getConfidenceBadge = (score: number) => {
    if (score >= 0.8) return { variant: 'default' as const, label: 'High Confidence' };
    if (score >= 0.6) return { variant: 'secondary' as const, label: 'Medium Confidence' };
    return { variant: 'destructive' as const, label: 'Low Confidence' };
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  if (!approval) return null;

  const confidenceBadge = getConfidenceBadge(approval.confidence_score);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-blue-600" />
                Transaction Details
              </DialogTitle>
              <DialogDescription>
                Review and edit the extracted transaction information before approval
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={confidenceBadge.variant}>
                {confidenceBadge.label}
              </Badge>
              <span className="text-sm font-medium">
                {Math.round(approval.confidence_score * 100)}%
              </span>
            </div>
          </div>
        </DialogHeader>

        {/* Email Information */}
        <div className="border rounded-lg p-4 bg-muted/20">
          <h4 className="font-medium mb-2">Email Information</h4>
          <div className="space-y-1 text-sm">
            <p><span className="font-medium">Subject:</span> {approval.email_message?.subject || 'Unknown'}</p>
            <p><span className="font-medium">From:</span> {approval.email_message?.sender || 'Unknown'}</p>
            <p><span className="font-medium">Received:</span> {approval.email_message?.received_at ? formatDate(approval.email_message.received_at) : 'Unknown'}</p>
            <p><span className="font-medium">Source:</span> {approval.extracted_data.source}</p>
          </div>
        </div>

        {/* Low Confidence Warning */}
        {approval.confidence_score < 0.6 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              This transaction has low confidence. Please review the extracted data carefully before approving.
            </AlertDescription>
          </Alert>
        )}

        {/* Transaction Detail Form */}
        <div className="flex-1 overflow-hidden">
          <TransactionDetailForm
            approval={approval}
            formData={formData}
            onFormChange={handleFormChange}
            onApprove={handleApprove}
            onReject={handleReject}
            isProcessing={isProcessing}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TransactionDetailModal;
