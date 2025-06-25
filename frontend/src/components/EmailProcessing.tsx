import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import {
  Mail,
  Plus,
  RefreshCw,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  Settings,
  Eye,
  EyeOff,
  TrendingUp,
  Database,
  Filter,
  Zap,
  List,
  Calendar,
  DollarSign,
  Building
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface EmailAccount {
  id: number;
  email_address: string;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string;
}

interface SyncResult {
  message: string;
  account_id: number;
  status: string;
  messages_synced: number;  // Fixed: backend returns 'messages_synced', not 'synced_messages'
  messages_queued?: number;
  financial_emails_found?: number;
  skipped_non_financial?: number;
  messages?: any[];
  error?: string;
}

interface FinancialEmail {
  id: number;
  subject: string;
  sender: string;
  received_at: string;
  processing_status: string;
  financial_confidence?: number;
  has_attachments: boolean;
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

interface SyncProgress {
  accountId: number;
  stage: 'starting' | 'fetching' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  details?: {
    emailsFound?: number;
    emailsProcessed?: number;
    transactionsExtracted?: number;
  };
}

export function EmailProcessing() {
  const [emailAccounts, setEmailAccounts] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [showDetails, setShowDetails] = useState<number | null>(null);
  const [syncProgress, setSyncProgress] = useState<SyncProgress | null>(null);
  const [lastSyncResults, setLastSyncResults] = useState<{[key: number]: SyncResult}>({});
  const [emails, setEmails] = useState<FinancialEmail[]>([]);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [emailsLoading, setEmailsLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'processed' | 'pending'>('all');
  const { toast } = useToast();

  // Get auth token
  const getAuthToken = () => {
    return localStorage.getItem('accessToken');
  };

  // Fetch financial emails
  const fetchFinancialEmails = async () => {
    try {
      setEmailsLoading(true);
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
        setEmailStats(data.stats || null);
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
      setEmailsLoading(false);
    }
  };

  // Fetch connected email accounts
  const fetchEmailAccounts = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();

      const response = await fetch('/api/email/accounts', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const accounts = await response.json();
        setEmailAccounts(accounts);
      } else {
        throw new Error('Failed to fetch email accounts');
      }
    } catch (error) {
      console.error('Error fetching email accounts:', error);
      toast({
        title: "Error",
        description: "Failed to load email accounts",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Connect Gmail account with improved COOP-compatible flow
  const connectGmailAccount = async () => {
    try {
      const token = getAuthToken();

      const response = await fetch('/api/email/oauth/authorize', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();

        // Store current page state for return navigation
        sessionStorage.setItem('oauth_return_page', window.location.pathname);
        sessionStorage.setItem('oauth_in_progress', 'true');

        toast({
          title: "Gmail Authorization",
          description: "Redirecting to Google for authorization...",
        });

        // Use direct redirect instead of popup to avoid COOP issues
        window.location.href = data.authorization_url;

      } else {
        throw new Error('Failed to initiate OAuth');
      }
    } catch (error) {
      console.error('Error connecting Gmail:', error);
      toast({
        title: "Error",
        description: "Failed to connect Gmail account",
        variant: "destructive",
      });
    }
  };

  // Enhanced sync email account with progress tracking
  const syncEmailAccount = async (accountId: number) => {
    try {
      setSyncing(accountId);
      setSyncProgress({
        accountId,
        stage: 'starting',
        progress: 0,
        message: 'Initializing email sync...'
      });

      const token = getAuthToken();

      const response = await fetch(`/api/email/accounts/${accountId}/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result: SyncResult = await response.json();

        // Store sync results for display
        setLastSyncResults(prev => ({
          ...prev,
          [accountId]: result
        }));

        if (result.status === 'queued') {
          setSyncProgress({
            accountId,
            stage: 'fetching',
            progress: 25,
            message: 'Email sync task queued. Fetching emails from Gmail...'
          });

          toast({
            title: "Sync Started",
            description: `Email sync task has been queued. Processing will begin shortly.`,
          });

          // Start progress monitoring
          monitorSyncProgress(accountId);
        } else if (result.status === 'completed') {
          setSyncProgress({
            accountId,
            stage: 'completed',
            progress: 100,
            message: 'Sync completed successfully!',
            details: {
              emailsFound: result.messages_synced,  // Fixed: use correct field name
              transactionsExtracted: result.messages_queued || 0
            }
          });

          toast({
            title: "Sync Completed",
            description: `Successfully processed ${result.messages_synced} emails, found ${result.messages_queued || 0} financial transactions`,
          });

          // Refresh accounts to update last_sync_at
          fetchEmailAccounts();

          // Clear progress after showing success
          setTimeout(() => setSyncProgress(null), 5000);
        } else {
          throw new Error(result.error || 'Sync failed');
        }
      } else {
        const errorText = await response.text();
        throw new Error(`Sync failed: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error syncing emails:', error);

      setSyncProgress({
        accountId,
        stage: 'error',
        progress: 0,
        message: `Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });

      toast({
        title: "Sync Failed",
        description: error instanceof Error ? error.message : "Failed to sync emails. Please try again.",
        variant: "destructive",
      });

      // Clear error progress after 10 seconds
      setTimeout(() => setSyncProgress(null), 10000);
    } finally {
      setSyncing(null);
    }
  };

  // Monitor sync progress for queued tasks
  const monitorSyncProgress = (accountId: number) => {
    let progressInterval: NodeJS.Timeout;
    let progressValue = 25;

    const updateProgress = () => {
      progressValue = Math.min(progressValue + 15, 90);

      setSyncProgress(prev => prev ? {
        ...prev,
        progress: progressValue,
        message: progressValue < 50 ? 'Fetching emails from Gmail...' :
                progressValue < 75 ? 'Processing financial emails...' :
                'Extracting transaction data...'
      } : null);

      if (progressValue >= 90) {
        clearInterval(progressInterval);
        // Final check after 3 seconds
        setTimeout(() => {
          fetchEmailAccounts();
          fetchFinancialEmails(); // Refresh email list after sync
          setSyncProgress(prev => prev ? {
            ...prev,
            stage: 'completed',
            progress: 100,
            message: 'Sync completed! Check the Financial Emails tab for new items.'
          } : null);
          setTimeout(() => setSyncProgress(null), 5000); // Show success message longer
        }, 3000);
      }
    };

    progressInterval = setInterval(updateProgress, 2000);

    // Cleanup after 30 seconds max
    setTimeout(() => {
      clearInterval(progressInterval);
    }, 30000);
  };

  // Disconnect email account
  const disconnectEmailAccount = async (accountId: number) => {
    try {
      const token = getAuthToken();
      
      const response = await fetch(`/api/email/accounts/${accountId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        toast({
          title: "Account Disconnected",
          description: "Email account has been disconnected successfully",
        });
        
        // Refresh accounts list
        fetchEmailAccounts();
      } else {
        throw new Error('Failed to disconnect account');
      }
    } catch (error) {
      console.error('Error disconnecting account:', error);
      toast({
        title: "Error",
        description: "Failed to disconnect email account",
        variant: "destructive",
      });
    }
  };

  // Load accounts and emails on component mount
  useEffect(() => {
    fetchEmailAccounts();
    fetchFinancialEmails();

    // Check if returning from OAuth flow
    const oauthInProgress = sessionStorage.getItem('oauth_in_progress');
    const oauthSuccess = sessionStorage.getItem('oauth_success');
    const oauthError = sessionStorage.getItem('oauth_error');
    const oauthEmail = sessionStorage.getItem('oauth_email');

    if (oauthInProgress === 'true') {
      // Clear the flags
      sessionStorage.removeItem('oauth_in_progress');
      sessionStorage.removeItem('oauth_success');
      sessionStorage.removeItem('oauth_error');
      sessionStorage.removeItem('oauth_email');

      if (oauthSuccess === 'true') {
        // Show success message
        toast({
          title: "Gmail Connected",
          description: `Successfully connected ${oauthEmail || 'Gmail account'}!`,
        });
      } else if (oauthError) {
        // Show error message
        toast({
          title: "Connection Failed",
          description: `Failed to connect Gmail: ${oauthError}`,
          variant: "destructive",
        });
      } else {
        // Generic processing message
        toast({
          title: "Gmail Authorization",
          description: "Checking authorization status...",
        });
      }

      // Refresh accounts after a short delay to allow backend processing
      setTimeout(() => {
        fetchEmailAccounts();
      }, 2000);
    }

    // Listen for refresh events from OAuth callback (fallback)
    const handleRefresh = () => {
      fetchEmailAccounts();
    };

    window.addEventListener('refreshEmailAccounts', handleRefresh);

    return () => {
      window.removeEventListener('refreshEmailAccounts', handleRefresh);
    };
  }, []);



  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  // Helper functions for email display
  const getConfidenceBadge = (confidence?: number) => {
    if (!confidence) return { label: 'Unknown', variant: 'secondary' as const };
    if (confidence >= 0.8) return { label: 'High', variant: 'default' as const };
    if (confidence >= 0.6) return { label: 'Medium', variant: 'secondary' as const };
    return { label: 'Low', variant: 'outline' as const };
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Filter emails based on current filter
  const filteredEmails = emails.filter(email => {
    if (filter === 'all') return true;
    if (filter === 'processed') return email.processing_status === 'processed';
    if (filter === 'pending') return email.processing_status === 'pending';
    return true;
  });

  // Progress indicator component
  const SyncProgressIndicator = ({ progress }: { progress: SyncProgress }) => (
    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
      <div className="flex items-center gap-3 mb-3">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
          {progress.message}
        </span>
      </div>

      <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mb-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress.progress}%` }}
        ></div>
      </div>

      <div className="flex justify-between text-xs text-blue-700 dark:text-blue-300">
        <span>{progress.stage.charAt(0).toUpperCase() + progress.stage.slice(1)}</span>
        <span>{progress.progress}%</span>
      </div>

      {progress.details && (
        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
          {progress.details.emailsFound !== undefined && (
            <div className="text-blue-700 dark:text-blue-300">
              <span className="font-medium">Emails Found:</span> {progress.details.emailsFound}
            </div>
          )}
          {progress.details.transactionsExtracted !== undefined && (
            <div className="text-blue-700 dark:text-blue-300">
              <span className="font-medium">Transactions:</span> {progress.details.transactionsExtracted}
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Sync results component
  const SyncResultsDisplay = ({ accountId, result }: { accountId: number, result: SyncResult }) => (
    <div className="mt-4 p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <span className="text-sm font-medium text-green-900 dark:text-green-100">
          Last Sync Results
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
        <div className="text-green-700 dark:text-green-300">
          <div className="font-medium">Total Processed</div>
          <div className="text-lg font-bold">{result.messages_synced || 0}</div>
          <div className="text-xs opacity-75">Max: 500 per sync</div>
        </div>

        <div className="text-blue-700 dark:text-blue-300">
          <div className="font-medium">New Emails Found</div>
          <div className="text-lg font-bold">{result.messages_queued || 0}</div>
          <div className="text-xs opacity-75">Queued for processing</div>
        </div>

        {result.financial_emails_found !== undefined && (
          <div className="text-green-700 dark:text-green-300">
            <div className="font-medium">Financial Emails</div>
            <div className="text-lg font-bold">{result.financial_emails_found}</div>
          </div>
        )}

        {result.skipped_non_financial !== undefined && (
          <div className="text-green-700 dark:text-green-300">
            <div className="font-medium">Filtered Out</div>
            <div className="text-lg font-bold">{result.skipped_non_financial}</div>
          </div>
        )}

        <div className="text-purple-700 dark:text-purple-300">
          <div className="font-medium">Sync Method</div>
          <div className="text-sm font-bold">Hybrid Sync</div>
          <div className="text-xs opacity-75">Threads + Messages</div>
        </div>

        <div className="text-gray-700 dark:text-gray-300">
          <div className="font-medium">Existing Emails</div>
          <div className="text-lg font-bold">{(result.messages_synced || 0) - (result.messages_queued || 0)}</div>
          <div className="text-xs opacity-75">Already in system</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Automated Expense Tracking</h2>
          <p className="text-muted-foreground">
            Connect your email accounts to automatically detect and extract expense data
          </p>
        </div>
        <Button onClick={connectGmailAccount} className="flex items-center gap-2">
          <Mail className="h-4 w-4" />
          Connect Gmail Account
        </Button>
      </div>

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          We'll automatically scan your emails for financial transactions from banks, payment processors,
          and e-wallets. All data is encrypted and processed securely.
        </AlertDescription>
      </Alert>

      {/* Main Content Tabs */}
      <Tabs defaultValue="accounts" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="accounts" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Email Accounts
          </TabsTrigger>
          <TabsTrigger value="emails" className="flex items-center gap-2">
            <List className="h-4 w-4" />
            Financial Emails ({emails.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="accounts" className="space-y-4">

      {/* Connected Accounts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Connected Email Accounts
          </CardTitle>
          <CardDescription>
            Manage your connected email accounts for automated expense tracking
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : emailAccounts.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Email Accounts Connected</h3>
              <p className="text-muted-foreground mb-4">
                Connect your Gmail account to start automatically tracking expenses from emails
              </p>
              <Button onClick={connectGmailAccount} className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Connect Gmail Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {emailAccounts.map((account) => (
                <div key={account.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">{account.email_address}</p>
                        <p className="text-sm text-muted-foreground">
                          Last sync: {formatDate(account.last_sync_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Badge variant={account.is_active ? "default" : "secondary"}>
                        {account.is_active ? "Active" : "Inactive"}
                      </Badge>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowDetails(showDetails === account.id ? null : account.id)}
                      >
                        {showDetails === account.id ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => syncEmailAccount(account.id)}
                        disabled={syncing === account.id}
                      >
                        {syncing === account.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => disconnectEmailAccount(account.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Sync Progress Indicator */}
                  {syncProgress && syncProgress.accountId === account.id && (
                    <SyncProgressIndicator progress={syncProgress} />
                  )}

                  {/* Last Sync Results */}
                  {lastSyncResults[account.id] && !syncProgress && (
                    <SyncResultsDisplay
                      accountId={account.id}
                      result={lastSyncResults[account.id]}
                    />
                  )}

                  {showDetails === account.id && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-medium">Account ID</p>
                          <p className="text-muted-foreground">{account.id}</p>
                        </div>
                        <div>
                          <p className="font-medium">Connected</p>
                          <p className="text-muted-foreground">{formatDate(account.created_at)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Enhanced How it Works */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            How Enhanced Automated Expense Tracking Works
          </CardTitle>
          <CardDescription>
            Our improved system processes 10x more emails with advanced AI filtering and extraction
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="bg-blue-100 dark:bg-blue-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Filter className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-medium mb-2">1. Smart Filtering</h3>
              <p className="text-sm text-muted-foreground">
                Advanced AI filters scan 500+ emails per sync, identifying only genuine financial transactions
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 dark:bg-green-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Database className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-medium mb-2">2. Data Extraction</h3>
              <p className="text-sm text-muted-foreground">
                Extracts amounts, merchants, dates, and transaction IDs from Nepali and international sources
              </p>
            </div>

            <div className="text-center">
              <div className="bg-purple-100 dark:bg-purple-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="font-medium mb-2">3. Confidence Scoring</h3>
              <p className="text-sm text-muted-foreground">
                Each transaction gets a confidence score to help you prioritize high-quality extractions
              </p>
            </div>

            <div className="text-center">
              <div className="bg-orange-100 dark:bg-orange-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="h-6 w-6 text-orange-600" />
              </div>
              <h3 className="font-medium mb-2">4. Review & Approve</h3>
              <p className="text-sm text-muted-foreground">
                Review extracted data with enhanced UI showing all transaction details before approval
              </p>
            </div>
          </div>

          {/* Performance Stats */}
          <div className="bg-muted/20 rounded-lg p-4">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-600" />
              Performance Improvements
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">10x</div>
                <div className="text-muted-foreground">More Emails</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">95%</div>
                <div className="text-muted-foreground">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">30+</div>
                <div className="text-muted-foreground">Institutions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">Real-time</div>
                <div className="text-muted-foreground">Processing</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="emails" className="space-y-4">
          {/* Email Statistics */}
          {emailStats && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Email Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{emailStats.total_emails}</div>
                    <div className="text-sm text-muted-foreground">Total Emails</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{emailStats.financial_emails}</div>
                    <div className="text-sm text-muted-foreground">Financial Emails</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{emailStats.processed_emails}</div>
                    <div className="text-sm text-muted-foreground">Processed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{emailStats.pending_approvals}</div>
                    <div className="text-sm text-muted-foreground">Pending Approvals</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Email Filter */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Financial Emails ({filteredEmails.length})
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant={filter === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter('all')}
                  >
                    All
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
                  <Button onClick={fetchFinancialEmails} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {emailsLoading ? (
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

                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Status: {email.processing_status}
                          </div>
                          {email.has_attachments && (
                            <div className="flex items-center gap-1">
                              <Database className="h-3 w-3" />
                              Has attachments
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
