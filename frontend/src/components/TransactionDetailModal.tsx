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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Mail,
  AlertTriangle,
  X,
  Calendar,
  Building,
  DollarSign,
  Eye,
  FileText,
  EyeOff
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import TransactionDetailForm from './TransactionDetailForm';

interface EmailContent {
  id: number;
  message_id: string;
  subject: string;
  sender: string;
  received_at: string;
  body_text: string;
  body_html: string;
  has_attachments: boolean;
  attachments: any[];
}

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
  const [emailContent, setEmailContent] = useState<EmailContent | null>(null);
  const [loadingEmailContent, setLoadingEmailContent] = useState(false);
  const [showEmailContent, setShowEmailContent] = useState(false);
  const { toast } = useToast();

  // Fetch email content
  const fetchEmailContent = async (messageId: number) => {
    if (!messageId) return;

    setLoadingEmailContent(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`/api/email/messages/${messageId}/content`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const content = await response.json();
        setEmailContent(content);
      } else {
        console.error('Failed to fetch email content');
        toast({
          title: "Error",
          description: "Failed to load email content",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error fetching email content:', error);
      toast({
        title: "Error",
        description: "Failed to load email content",
        variant: "destructive",
      });
    } finally {
      setLoadingEmailContent(false);
    }
  };

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

      // Reset email content state
      setEmailContent(null);
      setShowEmailContent(false);

      // Fetch email content if available
      if (approval.email_message_id) {
        fetchEmailContent(approval.email_message_id);
      }
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
      <DialogContent className="max-w-5xl max-h-[95vh] h-[95vh] overflow-hidden flex flex-col">
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

        {/* Low Confidence Warning */}
        {approval.confidence_score < 0.6 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              This transaction has low confidence. Please review the extracted data carefully before approving.
            </AlertDescription>
          </Alert>
        )}

        {/* Tabbed Content */}
        <div className="flex-1 overflow-hidden">
          <Tabs defaultValue="transaction" className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="transaction" className="flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Transaction Details
              </TabsTrigger>
              <TabsTrigger value="email" className="flex items-center gap-2" disabled={!approval.email_message_id}>
                <FileText className="h-4 w-4" />
                Original Email
                {loadingEmailContent && <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary ml-1"></div>}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="transaction" className="flex-1 overflow-hidden mt-4">
              <TransactionDetailForm
                approval={approval}
                formData={formData}
                onFormChange={handleFormChange}
                onApprove={handleApprove}
                onReject={handleReject}
                isProcessing={isProcessing}
              />
            </TabsContent>

            <TabsContent value="email" className="flex-1 overflow-hidden mt-4">
              {emailContent ? (
                <div className="h-full flex flex-col space-y-3">
                  {/* Email Header - Compact */}
                  <div className="border rounded-lg p-3 bg-muted/20 flex-shrink-0">
                    <h4 className="font-medium mb-2 flex items-center gap-2 text-sm">
                      <Mail className="h-4 w-4" />
                      Email Information
                    </h4>
                    <div className="grid grid-cols-1 gap-1 text-xs">
                      <p><span className="font-medium">Subject:</span> <span className="text-muted-foreground">{emailContent.subject}</span></p>
                      <p><span className="font-medium">From:</span> <span className="text-muted-foreground">{emailContent.sender}</span></p>
                      <p><span className="font-medium">Received:</span> <span className="text-muted-foreground">{formatDate(emailContent.received_at)}</span></p>
                      {emailContent.has_attachments && (
                        <p><span className="font-medium">Attachments:</span> <span className="text-muted-foreground">{emailContent.attachments?.length || 0} file(s)</span></p>
                      )}
                    </div>
                  </div>

                  {/* Email Content - Scrollable */}
                  <div className="flex-1 min-h-0">
                    <div className="border rounded-lg bg-background h-full flex flex-col">
                      <div className="p-3 border-b flex-shrink-0">
                        <h5 className="font-medium text-sm">Email Content</h5>
                      </div>
                      <ScrollArea className="flex-1 p-3">
                        <div className="prose prose-sm max-w-none">
                          {emailContent.body_html ? (
                            <div
                              dangerouslySetInnerHTML={{ __html: emailContent.body_html }}
                              className="text-xs leading-relaxed [&_*]:text-xs [&_*]:leading-relaxed"
                              style={{ fontSize: '12px', lineHeight: '1.4' }}
                            />
                          ) : (
                            <pre className="whitespace-pre-wrap text-xs leading-relaxed font-sans">
                              {emailContent.body_text || 'No content available'}
                            </pre>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </div>
                </div>
              ) : loadingEmailContent ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Loading email content...</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">Email content not available</p>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TransactionDetailModal;
