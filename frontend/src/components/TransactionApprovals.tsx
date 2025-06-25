import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
  MousePointer,
  RefreshCw,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
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
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [sortBy, setSortBy] = useState<'date' | 'confidence' | 'status'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { toast } = useToast();

  // Get auth token
  const getAuthToken = () => {
    return localStorage.getItem('accessToken');
  };

  // Enhanced fetch transaction approvals with better error handling
  const fetchTransactionApprovals = async (status?: string) => {
    try {
      setLoading(true);
      const token = getAuthToken();

      if (!token) {
        throw new Error('Authentication token not found. Please log in again.');
      }

      const currentStatus = status || statusFilter;
      console.log(`🔍 Fetching transaction approvals with status: ${currentStatus}`);

      // Build URL with status filter (empty string means all statuses)
      const url = currentStatus === 'ALL'
        ? '/api/email/approvals'
        : `/api/email/approvals?status=${currentStatus}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 API Response:', response.status, response.statusText);

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Received data:', data);

        // Validate data structure
        if (Array.isArray(data)) {
          setApprovals(data);

          // Show success message if we have new approvals
          if (data.length > 0) {
            toast({
              title: "Approvals Loaded",
              description: `Found ${data.length} pending transaction${data.length !== 1 ? 's' : ''} for review`,
            });
          }
        } else {
          console.warn('⚠️ Unexpected data format:', data);
          setApprovals([]);
        }
      } else {
        const errorText = await response.text();
        console.error('❌ API Error:', response.status, errorText);

        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        } else if (response.status === 403) {
          throw new Error('Access denied. You may not have permission to view transaction approvals.');
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later.');
        } else {
          throw new Error(`Failed to fetch transaction approvals: ${response.status}`);
        }
      }
    } catch (error) {
      console.error('Error fetching approvals:', error);

      const errorMessage = error instanceof Error ? error.message : 'Failed to load transaction approvals';

      toast({
        title: "Error Loading Approvals",
        description: errorMessage,
        variant: "destructive",
      });

      // Clear approvals on error
      setApprovals([]);
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

  // Sort approvals based on current sort settings
  const sortApprovals = (approvalsToSort: TransactionApproval[]) => {
    return [...approvalsToSort].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'confidence':
          comparison = a.confidence_score - b.confidence_score;
          break;
        case 'status':
          comparison = a.approval_status.localeCompare(b.approval_status);
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });
  };

  // Load approvals on component mount and when filters change
  useEffect(() => {
    fetchTransactionApprovals();
  }, [statusFilter]);

  // Sort approvals when sort settings change
  useEffect(() => {
    setApprovals(prev => sortApprovals(prev));
  }, [sortBy, sortOrder]);

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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Transaction Approvals</h2>
          <p className="text-muted-foreground">
            Review and approve automatically extracted transactions from your emails
          </p>
        </div>
        <Button
          onClick={() => fetchTransactionApprovals()}
          variant="outline"
          disabled={loading}
          className="flex items-center gap-2"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {/* Filters and Sorting */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Status:</span>
              <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value)}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort By */}
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Sort by:</span>
              <Select value={sortBy} onValueChange={(value: 'date' | 'confidence' | 'status') => setSortBy(value)}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="confidence">Confidence</SelectItem>
                  <SelectItem value="status">Status</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort Order */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="flex items-center gap-2"
            >
              {sortOrder === 'asc' ? (
                <ArrowUp className="h-4 w-4" />
              ) : (
                <ArrowDown className="h-4 w-4" />
              )}
              {sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            </Button>

            {/* Results Count */}
            <div className="ml-auto text-sm text-muted-foreground">
              {approvals.length} transaction{approvals.length !== 1 ? 's' : ''} found
            </div>
          </div>
        </CardContent>
      </Card>

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
            {statusFilter === 'ALL' ? 'All Transactions' :
             statusFilter === 'PENDING' ? 'Pending Approvals' :
             statusFilter === 'APPROVED' ? 'Approved Transactions' :
             'Rejected Transactions'}
          </CardTitle>
          <CardDescription>
            {statusFilter === 'PENDING'
              ? 'Review extracted transaction data before adding to your expenses'
              : statusFilter === 'APPROVED'
              ? 'Successfully approved and processed transactions'
              : statusFilter === 'REJECTED'
              ? 'Transactions that were rejected during review'
              : 'All transaction approvals across all statuses'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : approvals.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-xl font-medium mb-2">
                {statusFilter === 'ALL' ? 'No Transactions Found' :
                 statusFilter === 'PENDING' ? 'No Pending Approvals' :
                 statusFilter === 'APPROVED' ? 'No Approved Transactions' :
                 'No Rejected Transactions'}
              </h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                {statusFilter === 'PENDING'
                  ? 'All extracted transactions have been reviewed. New transactions will appear here automatically when financial emails are processed.'
                  : statusFilter === 'APPROVED'
                  ? 'No transactions have been approved yet. Approve pending transactions to see them here.'
                  : statusFilter === 'REJECTED'
                  ? 'No transactions have been rejected yet.'
                  : 'No transactions found. Try syncing your email accounts or check different status filters.'
                }
              </p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  onClick={fetchTransactionApprovals}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Check for New Approvals
                </Button>

                <Button
                  onClick={() => window.location.href = '/email-processing'}
                  variant="default"
                  className="flex items-center gap-2"
                >
                  <Mail className="h-4 w-4" />
                  Sync Email Accounts
                </Button>
              </div>

              <div className="mt-6 p-4 bg-muted/20 rounded-lg max-w-md mx-auto">
                <p className="text-sm text-muted-foreground">
                  💡 <strong>Tip:</strong> Make sure your email accounts are connected and synced to automatically detect financial transactions.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {approvals.map((approval) => {
                const confidenceBadge = getConfidenceBadge(approval.confidence_score);

                return (
                  <div
                    key={approval.id}
                    className="border rounded-xl p-6 cursor-pointer hover:bg-muted/20 hover:border-primary/50 hover:shadow-md transition-all duration-200 bg-card"
                    onClick={() => handleTransactionClick(approval)}
                  >
                    {/* Click hint */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 px-3 py-1 rounded-full">
                        <MousePointer className="h-3 w-3" />
                        <span>Click to view details and edit</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            approval.approval_status === 'APPROVED' ? 'default' :
                            approval.approval_status === 'PENDING' ? 'secondary' :
                            'destructive'
                          }
                          className="text-xs"
                        >
                          {approval.approval_status}
                        </Badge>
                        <Badge variant={confidenceBadge.variant} className="text-xs">
                          {confidenceBadge.label}
                        </Badge>
                        <span className={`text-sm font-semibold ${getConfidenceColor(approval.confidence_score)}`}>
                          {Math.round(approval.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Header */}
                    <div className="mb-6">
                      <div className="flex items-start gap-4">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                            <Mail className="h-6 w-6 text-blue-600" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-foreground mb-2 truncate">
                            {approval.email_message?.subject || 'Email Transaction'}
                          </h3>
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">
                              <span className="font-medium">From:</span> {approval.email_message?.sender || 'Unknown'}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              <span className="font-medium">Received:</span> {approval.email_message?.received_at ? formatDate(approval.email_message.received_at) : 'Unknown'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Extracted Data */}
                    <div className="bg-muted/20 rounded-lg p-4 mb-6">
                      <h4 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        Extracted Transaction Data
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Amounts */}
                        {approval.extracted_data.amounts && approval.extracted_data.amounts.length > 0 && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                                <DollarSign className="h-4 w-4 text-green-600" />
                              </div>
                              <span className="text-sm font-semibold text-foreground">Amounts</span>
                            </div>
                            <div className="space-y-1">
                              {approval.extracted_data.amounts.map((amount, index) => (
                                <p key={index} className="text-sm text-foreground bg-white px-3 py-1 rounded border">
                                  {amount}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Dates */}
                        {approval.extracted_data.dates && approval.extracted_data.dates.length > 0 && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <Calendar className="h-4 w-4 text-blue-600" />
                              </div>
                              <span className="text-sm font-semibold text-foreground">Dates</span>
                            </div>
                            <div className="space-y-1">
                              {approval.extracted_data.dates.map((date, index) => (
                                <p key={index} className="text-sm text-foreground bg-white px-3 py-1 rounded border">
                                  {date}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Merchants */}
                        {approval.extracted_data.merchants && approval.extracted_data.merchants.length > 0 && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                                <Building className="h-4 w-4 text-purple-600" />
                              </div>
                              <span className="text-sm font-semibold text-foreground">Merchants</span>
                            </div>
                            <div className="space-y-1">
                              {approval.extracted_data.merchants.map((merchant, index) => (
                                <p key={index} className="text-sm text-foreground bg-white px-3 py-1 rounded border">
                                  {merchant}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Transaction IDs */}
                        {approval.extracted_data.transaction_ids && approval.extracted_data.transaction_ids.length > 0 && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                                <Eye className="h-4 w-4 text-orange-600" />
                              </div>
                              <span className="text-sm font-semibold text-foreground">Transaction IDs</span>
                            </div>
                            <div className="space-y-1">
                              {approval.extracted_data.transaction_ids.map((id, index) => (
                                <p key={index} className="text-sm text-foreground bg-white px-3 py-1 rounded border font-mono">
                                  {id}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Low Confidence Warning */}
                    {approval.confidence_score < 0.6 && (
                      <Alert className="mb-6 border-amber-200 bg-amber-50">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        <AlertDescription className="text-amber-800">
                          This transaction has low confidence. Please review the extracted data carefully before approving.
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 pt-6 border-t border-border">
                      {approval.approval_status === 'PENDING' ? (
                        <>
                          <Button
                            onClick={(e) => {
                              e.stopPropagation();
                              approveTransaction(approval.id);
                            }}
                            disabled={processing === approval.id}
                            className="flex items-center gap-2 px-4 py-2"
                            size="default"
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
                            className="flex items-center gap-2 px-4 py-2"
                            size="default"
                          >
                            <ThumbsDown className="h-4 w-4" />
                            Quick Reject
                          </Button>
                        </>
                      ) : (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <CheckCircle className="h-4 w-4" />
                          <span>
                            Transaction {approval.approval_status.toLowerCase()} on{' '}
                            {formatDate(approval.created_at)}
                          </span>
                        </div>
                      )}

                      <Button
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTransactionClick(approval);
                        }}
                        disabled={processing === approval.id}
                        className="flex items-center gap-2 ml-auto px-4 py-2"
                        size="default"
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
