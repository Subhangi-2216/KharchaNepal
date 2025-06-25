import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Mail,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  Eye,
  Filter,
  Calendar,
  DollarSign,
  Building
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface FinancialEmail {
  id: number;
  subject: string;
  sender: string;
  received_at: string;
  has_attachments: boolean;
  processing_status: 'PENDING' | 'PROCESSING' | 'PROCESSED';
  financial_confidence?: number;
  extracted_data?: {
    amounts?: string[];
    merchants?: string[];
    dates?: string[];
    transaction_ids?: string[];
  };
}

interface EmailStats {
  total_emails: number;
  financial_emails: number;
  processed_emails: number;
  pending_approvals: number;
  confidence_distribution: {
    high: number;
    medium: number;
    low: number;
  };
}

export function FinancialEmailsSection() {
  const [emails, setEmails] = useState<FinancialEmail[]>([]);
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'processed' | 'pending'>('all');
  const { toast } = useToast();

  // Get auth token
  const getAuthToken = () => {
    return localStorage.getItem('accessToken');
  };

  // Fetch financial emails
  const fetchFinancialEmails = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();

      const response = await fetch('/api/email/financial-emails', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setEmails(data.emails || []);
        setStats(data.stats || null);
      } else {
        throw new Error('Failed to fetch financial emails');
      }
    } catch (error) {
      console.error('Error fetching financial emails:', error);
      toast({
        title: "Error",
        description: "Failed to load financial emails",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchFinancialEmails();
  }, []);

  // Filter emails based on selected filter
  const filteredEmails = emails.filter(email => {
    if (filter === 'processed') return email.processing_status === 'PROCESSED';
    if (filter === 'pending') return email.processing_status === 'PENDING';
    return true;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (confidence?: number) => {
    if (!confidence) return { variant: 'secondary' as const, label: 'Unknown' };
    if (confidence >= 0.8) return { variant: 'default' as const, label: 'High' };
    if (confidence >= 0.6) return { variant: 'secondary' as const, label: 'Medium' };
    return { variant: 'destructive' as const, label: 'Low' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Financial Emails</h2>
          <p className="text-muted-foreground">
            Monitor and manage automatically detected financial emails
          </p>
        </div>
        <Button onClick={fetchFinancialEmails} variant="outline" className="flex items-center gap-2">
          <Mail className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-blue-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Total Emails</p>
                  <p className="text-2xl font-bold">{stats.total_emails}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Financial Emails</p>
                  <p className="text-2xl font-bold">{stats.financial_emails}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-purple-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Processed</p>
                  <p className="text-2xl font-bold">{stats.processed_emails}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-600" />
                <div>
                  <p className="text-sm text-muted-foreground">Pending Approvals</p>
                  <p className="text-2xl font-bold">{stats.pending_approvals}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="flex items-center gap-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          All Emails
        </Button>
        <Button
          variant={filter === 'processed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('processed')}
        >
          Processed
        </Button>
        <Button
          variant={filter === 'pending' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('pending')}
        >
          Pending
        </Button>
      </div>

      {/* Financial Emails List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Financial Emails ({filteredEmails.length})
          </CardTitle>
          <CardDescription>
            Emails automatically identified as containing financial transaction information
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Financial Emails Found</h3>
              <p className="text-muted-foreground">
                {filter === 'all' 
                  ? 'No financial emails have been detected yet. Try syncing your email accounts.'
                  : `No ${filter} financial emails found. Try changing the filter.`
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredEmails.map((email) => {
                const confidenceBadge = getConfidenceBadge(email.financial_confidence);
                
                return (
                  <div
                    key={email.id}
                    className="border rounded-lg p-4 hover:bg-muted/20 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{email.subject}</h3>
                        <p className="text-sm text-muted-foreground truncate">{email.sender}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(email.received_at)}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        <Badge variant={confidenceBadge.variant} className="text-xs">
                          {confidenceBadge.label}
                        </Badge>
                        {email.financial_confidence && (
                          <span className={`text-xs font-medium ${getConfidenceColor(email.financial_confidence)}`}>
                            {Math.round(email.financial_confidence * 100)}%
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Extracted Data Preview */}
                    {email.extracted_data && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        {email.extracted_data.amounts && email.extracted_data.amounts.length > 0 && (
                          <div>
                            <div className="flex items-center gap-1 mb-1">
                              <DollarSign className="h-3 w-3 text-green-600" />
                              <span className="font-medium">Amounts</span>
                            </div>
                            <div className="text-muted-foreground">
                              {email.extracted_data.amounts.slice(0, 2).join(', ')}
                              {email.extracted_data.amounts.length > 2 && '...'}
                            </div>
                          </div>
                        )}

                        {email.extracted_data.merchants && email.extracted_data.merchants.length > 0 && (
                          <div>
                            <div className="flex items-center gap-1 mb-1">
                              <Building className="h-3 w-3 text-purple-600" />
                              <span className="font-medium">Merchants</span>
                            </div>
                            <div className="text-muted-foreground">
                              {email.extracted_data.merchants.slice(0, 1).join(', ')}
                              {email.extracted_data.merchants.length > 1 && '...'}
                            </div>
                          </div>
                        )}

                        {email.extracted_data.dates && email.extracted_data.dates.length > 0 && (
                          <div>
                            <div className="flex items-center gap-1 mb-1">
                              <Calendar className="h-3 w-3 text-blue-600" />
                              <span className="font-medium">Dates</span>
                            </div>
                            <div className="text-muted-foreground">
                              {email.extracted_data.dates.slice(0, 1).join(', ')}
                            </div>
                          </div>
                        )}

                        {email.extracted_data.transaction_ids && email.extracted_data.transaction_ids.length > 0 && (
                          <div>
                            <div className="flex items-center gap-1 mb-1">
                              <Eye className="h-3 w-3 text-orange-600" />
                              <span className="font-medium">Transaction IDs</span>
                            </div>
                            <div className="text-muted-foreground font-mono">
                              {email.extracted_data.transaction_ids.slice(0, 1).join(', ')}
                              {email.extracted_data.transaction_ids.length > 1 && '...'}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Status and Actions */}
                    <div className="flex items-center justify-between mt-3 pt-3 border-t">
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant={email.processing_status === 'PROCESSED' ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {email.processing_status}
                        </Badge>
                        {email.has_attachments && (
                          <Badge variant="outline" className="text-xs">
                            Has Attachments
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default FinancialEmailsSection;
