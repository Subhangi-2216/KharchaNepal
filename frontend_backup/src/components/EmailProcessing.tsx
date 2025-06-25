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
  EyeOff
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
  messages?: any[];
  error?: string;
}

export function EmailProcessing() {
  const [emailAccounts, setEmailAccounts] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [showDetails, setShowDetails] = useState<number | null>(null);
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

  // Sync email account
  const syncEmailAccount = async (accountId: number) => {
    try {
      setSyncing(accountId);
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

        if (result.status === 'queued') {
          toast({
            title: "Sync Started",
            description: `Email sync task has been queued. Check back in a few moments.`,
          });

          // Refresh accounts to update last_sync_at after a delay
          setTimeout(() => {
            fetchEmailAccounts();
          }, 3000);
        } else if (result.status === 'completed') {
          toast({
            title: "Sync Completed",
            description: `Successfully synced ${result.synced_messages} financial emails`,
          });

          // Refresh accounts to update last_sync_at
          fetchEmailAccounts();
        } else {
          throw new Error(result.error || 'Sync failed');
        }
      } else {
        throw new Error('Failed to sync emails');
      }
    } catch (error) {
      console.error('Error syncing emails:', error);
      toast({
        title: "Sync Failed",
        description: "Failed to sync emails. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSyncing(null);
    }
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

      {/* How it Works */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            How Automated Expense Tracking Works
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="bg-blue-100 dark:bg-blue-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Mail className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-medium mb-2">1. Email Scanning</h3>
              <p className="text-sm text-muted-foreground">
                We scan your emails for financial transactions from banks, payment apps, and merchants
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 dark:bg-green-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-medium mb-2">2. Data Extraction</h3>
              <p className="text-sm text-muted-foreground">
                AI extracts transaction details like amount, merchant, date, and category automatically
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-orange-100 dark:bg-orange-900 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
              <h3 className="font-medium mb-2">3. Review & Approve</h3>
              <p className="text-sm text-muted-foreground">
                Review extracted transactions before they're added to your expense records
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
