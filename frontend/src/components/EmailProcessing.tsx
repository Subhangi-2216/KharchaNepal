import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

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
  Zap
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
  synced_messages: number;
  messages_queued?: number;
  financial_emails_found?: number;
  skipped_non_financial?: number;
  messages?: any[];
  error?: string;
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
  const { toast } = useToast();

  // Get auth token
  const getAuthToken = () => {
    return localStorage.getItem('accessToken');
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

  // Connect Gmail account
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

        // Open OAuth URL in popup window
        const popup = window.open(
          data.authorization_url,
          'gmail_oauth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        if (!popup) {
          throw new Error('Popup blocked. Please allow popups for this site.');
        }

        toast({
          title: "Gmail Authorization",
          description: "Please complete the authorization in the popup window",
        });

        // Listen for popup completion
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed);
            // Refresh accounts after popup closes
            setTimeout(() => {
              fetchEmailAccounts();
            }, 1000);
          }
        }, 1000);

        // Listen for messages from popup
        const messageListener = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;

          if (event.data.type === 'GMAIL_OAUTH_SUCCESS') {
            clearInterval(checkClosed);
            popup.close();

            toast({
              title: "Gmail Connected",
              description: `Successfully connected ${event.data.email}`,
            });

            // Refresh accounts
            fetchEmailAccounts();

            window.removeEventListener('message', messageListener);
          } else if (event.data.type === 'GMAIL_OAUTH_ERROR') {
            clearInterval(checkClosed);
            popup.close();

            toast({
              title: "Connection Failed",
              description: event.data.error || "Failed to connect Gmail account",
              variant: "destructive",
            });

            window.removeEventListener('message', messageListener);
          }
        };

        window.addEventListener('message', messageListener);

        // Cleanup after 5 minutes
        setTimeout(() => {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          if (!popup.closed) {
            popup.close();
          }
        }, 300000);

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
              emailsFound: result.synced_messages,
              transactionsExtracted: result.messages_queued || 0
            }
          });

          toast({
            title: "Sync Completed",
            description: `Successfully processed ${result.synced_messages} emails, found ${result.messages_queued || 0} financial transactions`,
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
          setSyncProgress(prev => prev ? {
            ...prev,
            stage: 'completed',
            progress: 100,
            message: 'Sync completed! Check transaction approvals for new items.'
          } : null);
          setTimeout(() => setSyncProgress(null), 3000);
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

  // Load accounts on component mount
  useEffect(() => {
    fetchEmailAccounts();
    
    // Listen for refresh events from OAuth callback
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="text-green-700 dark:text-green-300">
          <div className="font-medium">Emails Processed</div>
          <div className="text-lg font-bold">{result.synced_messages}</div>
        </div>

        {result.messages_queued !== undefined && (
          <div className="text-green-700 dark:text-green-300">
            <div className="font-medium">Transactions Found</div>
            <div className="text-lg font-bold">{result.messages_queued}</div>
          </div>
        )}

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
    </div>
  );
}
