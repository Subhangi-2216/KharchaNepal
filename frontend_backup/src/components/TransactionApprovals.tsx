import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CheckCircle,
  Clock,
  Mail,
  DollarSign,
  Calendar,
  Building,
  Eye,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  MousePointer
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import TransactionDetailModal from './TransactionDetailModal';

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

export function TransactionApprovals() {
  const [approvals, setApprovals] = useState<TransactionApproval[]>([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState<number | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<TransactionApproval | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { toast } = useToast();

  // Get auth token
  const getAuthToken = () => {
    return localStorage.getItem('accessToken');
  };

  // Fetch pending transaction approvals
  const fetchTransactionApprovals = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();

      console.log('🔍 Fetching transaction approvals...');
      console.log('Token:', token ? 'Present' : 'Missing');

      const response = await fetch('/api/email/approvals?status=PENDING', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 API Response:', response.status, response.statusText);

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Received data:', data);
        setApprovals(data);
      } else {
        const errorText = await response.text();
        console.error('❌ API Error:', response.status, errorText);
        throw new Error(`Failed to fetch transaction approvals: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching approvals:', error);
      toast({
        title: "Error",
        description: "Failed to load transaction approvals",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Approve transaction (with optional edited data)
  const approveTransaction = async (approvalId: number, editedData?: TransactionFormData) => {
    try {
      console.log('✅ Approving transaction:', approvalId, editedData);
      setProcessing(approvalId);
      const token = getAuthToken();

      const requestBody = editedData ? { edited_data: editedData } : {};

      const response = await fetch(`/api/email/approvals/${approvalId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('📡 Approve response:', response.status, response.statusText);

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Approval successful:', result);

        toast({
          title: "Transaction Approved",
          description: "Transaction has been added to your expenses",
        });

        // Remove from pending list
        setApprovals(prev => prev.filter(a => a.id !== approvalId));
      } else {
        const errorText = await response.text();
        console.error('❌ Approval failed:', response.status, errorText);
        throw new Error(`Failed to approve transaction: ${response.status}`);
      }
    } catch (error) {
      console.error('Error approving transaction:', error);
      toast({
        title: "Error",
        description: "Failed to approve transaction",
        variant: "destructive",
      });
    } finally {
      setProcessing(null);
    }
  };

  // Reject transaction
  const rejectTransaction = async (approvalId: number) => {
    try {
      console.log('❌ Rejecting transaction:', approvalId);
      setProcessing(approvalId);
      const token = getAuthToken();

      const response = await fetch(`/api/email/approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Reject response:', response.status, response.statusText);

      if (response.ok) {
        const result = await response.json();
        console.log('❌ Rejection successful:', result);

        toast({
          title: "Transaction Rejected",
          description: "Transaction has been rejected and will not be added to expenses",
        });

        // Remove from pending list
        setApprovals(prev => prev.filter(a => a.id !== approvalId));
      } else {
        const errorText = await response.text();
        console.error('❌ Rejection failed:', response.status, errorText);
        throw new Error(`Failed to reject transaction: ${response.status}`);
      }
    } catch (error) {
      console.error('Error rejecting transaction:', error);
      toast({
        title: "Error",
        description: "Failed to reject transaction",
        variant: "destructive",
      });
    } finally {
      setProcessing(null);
    }
  };

  // Handle opening transaction detail modal
  const handleTransactionClick = (approval: TransactionApproval) => {
    setSelectedApproval(approval);
    setIsModalOpen(true);
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedApproval(null);
  };

  // Load approvals on component mount
  useEffect(() => {
    fetchTransactionApprovals();
  }, []);

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (score: number) => {
    if (score >= 0.8) return { variant: 'default' as const, label: 'High Confidence' };
    if (score >= 0.6) return { variant: 'secondary' as const, label: 'Medium Confidence' };
    return { variant: 'destructive' as const, label: 'Low Confidence' };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Transaction Approvals</h2>
        <p className="text-muted-foreground">
          Review and approve automatically extracted transactions from your emails
        </p>
      </div>

      {/* Pending Count Alert */}
      {approvals.length > 0 && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            You have {approvals.length} pending transaction{approvals.length !== 1 ? 's' : ''} waiting for approval.
          </AlertDescription>
        </Alert>
      )}

      {/* Transaction Approvals List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Pending Approvals
          </CardTitle>
          <CardDescription>
            Review extracted transaction data before adding to your expenses
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : approvals.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Pending Approvals</h3>
              <p className="text-muted-foreground">
                All extracted transactions have been reviewed. New transactions will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {approvals.map((approval) => {
                const confidenceBadge = getConfidenceBadge(approval.confidence_score);
                
                return (
                  <div
                    key={approval.id}
                    className="border rounded-lg p-4 cursor-pointer hover:bg-muted/20 hover:border-primary/50 transition-colors"
                    onClick={() => handleTransactionClick(approval)}
                  >
                    {/* Click hint */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <MousePointer className="h-3 w-3" />
                        <span>Click to view details and edit</span>
                      </div>
                    </div>

                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-3">
                        <Mail className="h-5 w-5 text-blue-600 mt-1" />
                        <div>
                          <p className="font-medium">{approval.email_message?.subject || 'Email Transaction'}</p>
                          <p className="text-sm text-muted-foreground">
                            From: {approval.email_message?.sender || 'Unknown'}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Received: {approval.email_message?.received_at ? formatDate(approval.email_message.received_at) : 'Unknown'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge variant={confidenceBadge.variant}>
                          {confidenceBadge.label}
                        </Badge>
                        <span className={`text-sm font-medium ${getConfidenceColor(approval.confidence_score)}`}>
                          {Math.round(approval.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Extracted Data */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                      {/* Amounts */}
                      {approval.extracted_data.amounts && approval.extracted_data.amounts.length > 0 && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-green-600" />
                            <span className="text-sm font-medium">Amounts</span>
                          </div>
                          {approval.extracted_data.amounts.map((amount, index) => (
                            <p key={index} className="text-sm text-muted-foreground pl-6">
                              {amount}
                            </p>
                          ))}
                        </div>
                      )}

                      {/* Dates */}
                      {approval.extracted_data.dates && approval.extracted_data.dates.length > 0 && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-blue-600" />
                            <span className="text-sm font-medium">Dates</span>
                          </div>
                          {approval.extracted_data.dates.map((date, index) => (
                            <p key={index} className="text-sm text-muted-foreground pl-6">
                              {date}
                            </p>
                          ))}
                        </div>
                      )}

                      {/* Merchants */}
                      {approval.extracted_data.merchants && approval.extracted_data.merchants.length > 0 && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Building className="h-4 w-4 text-purple-600" />
                            <span className="text-sm font-medium">Merchants</span>
                          </div>
                          {approval.extracted_data.merchants.map((merchant, index) => (
                            <p key={index} className="text-sm text-muted-foreground pl-6">
                              {merchant}
                            </p>
                          ))}
                        </div>
                      )}

                      {/* Transaction IDs */}
                      {approval.extracted_data.transaction_ids && approval.extracted_data.transaction_ids.length > 0 && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Eye className="h-4 w-4 text-orange-600" />
                            <span className="text-sm font-medium">Transaction IDs</span>
                          </div>
                          {approval.extracted_data.transaction_ids.map((id, index) => (
                            <p key={index} className="text-sm text-muted-foreground pl-6 font-mono">
                              {id}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Low Confidence Warning */}
                    {approval.confidence_score < 0.6 && (
                      <Alert className="mb-4">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          This transaction has low confidence. Please review the extracted data carefully before approving.
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 pt-4 border-t">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          approveTransaction(approval.id);
                        }}
                        disabled={processing === approval.id}
                        className="flex items-center gap-2"
                        size="sm"
                      >
                        {processing === approval.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <ThumbsUp className="h-4 w-4" />
                        )}
                        Quick Approve
                      </Button>

                      <Button
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          rejectTransaction(approval.id);
                        }}
                        disabled={processing === approval.id}
                        className="flex items-center gap-2"
                        size="sm"
                      >
                        <ThumbsDown className="h-4 w-4" />
                        Quick Reject
                      </Button>

                      <Button
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTransactionClick(approval);
                        }}
                        disabled={processing === approval.id}
                        className="flex items-center gap-2 ml-auto"
                        size="sm"
                      >
                        <Eye className="h-4 w-4" />
                        View Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transaction Detail Modal */}
      <TransactionDetailModal
        open={isModalOpen}
        onOpenChange={handleModalClose}
        approval={selectedApproval}
        onApprove={approveTransaction}
        onReject={rejectTransaction}
        isProcessing={processing !== null}
      />
    </div>
  );
}
