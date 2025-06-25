import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Loader2, RefreshCw, TrendingUp, TrendingDown, Mail, CheckCircle, XCircle, Clock } from 'lucide-react';

interface DashboardData {
  generated_at: string;
  period_days: number;
  processing_overview: {
    period: {
      start_date: string;
      end_date: string;
      days: number;
    };
    totals: {
      total_emails: number;
      financial_emails: number;
      non_financial_emails: number;
      financial_detection_rate: number;
      processing_success_rate: number;
    };
    processing_status: Record<string, number>;
    approval_status: Record<string, number>;
  };
  detection_accuracy: {
    metrics: {
      total_detections: number;
      average_confidence: number;
      confidence_distribution: Record<string, number>;
      accuracy_by_confidence: Record<string, number>;
    };
  };
  extraction_quality: {
    metrics: {
      total_extractions: number;
      extraction_success_rates: Record<string, number>;
      average_patterns_per_email: Record<string, number>;
    };
  };
  sync_performance: {
    metrics: {
      total_accounts: number;
      accounts_with_errors: number;
      accounts_syncing: number;
      average_error_count: number;
      last_sync_distribution: Record<string, number>;
    };
  };
}

const EmailStatisticsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('7');

  const fetchDashboardData = async (days: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/email-processing/statistics/dashboard?days=${days}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData(selectedPeriod);
  }, [selectedPeriod]);

  const handleRefresh = () => {
    fetchDashboardData(selectedPeriod);
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;
  const formatNumber = (value: number) => value.toLocaleString();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center text-red-600">
              <XCircle className="h-5 w-5 mr-2" />
              <span>Error loading dashboard: {error}</span>
            </div>
            <Button onClick={handleRefresh} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const { processing_overview, detection_accuracy, extraction_quality, sync_performance } = dashboardData;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Email Processing Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Analytics for the last {dashboardData.period_days} days
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 Day</SelectItem>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
              <SelectItem value="90">90 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(processing_overview.totals.total_emails)}</div>
            <p className="text-xs text-muted-foreground">
              {formatNumber(processing_overview.totals.financial_emails)} financial
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detection Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercentage(processing_overview.totals.financial_detection_rate)}
            </div>
            <p className="text-xs text-muted-foreground">
              Financial emails detected
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Success</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercentage(processing_overview.totals.processing_success_rate)}
            </div>
            <p className="text-xs text-muted-foreground">
              Successfully processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(detection_accuracy.metrics.average_confidence * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Detection confidence
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Accuracy */}
        <Card>
          <CardHeader>
            <CardTitle>Detection Accuracy by Confidence</CardTitle>
            <CardDescription>
              Accuracy rates across different confidence levels
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(detection_accuracy.metrics.accuracy_by_confidence).map(([range, accuracy]) => (
                <div key={range} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{range}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${accuracy}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">{formatPercentage(accuracy)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Extraction Quality */}
        <Card>
          <CardHeader>
            <CardTitle>Extraction Success Rates</CardTitle>
            <CardDescription>
              Success rates for different data types
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(extraction_quality.metrics.extraction_success_rates).map(([field, rate]) => (
                <div key={field} className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize">{field}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${rate}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">{formatPercentage(rate)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Sync Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Sync Performance</CardTitle>
            <CardDescription>
              Email account synchronization status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Accounts</span>
                <Badge variant="outline">{sync_performance.metrics.total_accounts}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Currently Syncing</span>
                <Badge variant={sync_performance.metrics.accounts_syncing > 0 ? "default" : "secondary"}>
                  {sync_performance.metrics.accounts_syncing}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">With Errors</span>
                <Badge variant={sync_performance.metrics.accounts_with_errors > 0 ? "destructive" : "secondary"}>
                  {sync_performance.metrics.accounts_with_errors}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Avg Error Count</span>
                <span className="text-sm text-gray-600">
                  {sync_performance.metrics.average_error_count.toFixed(1)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Status */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Status</CardTitle>
            <CardDescription>
              Email processing status breakdown
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(processing_overview.processing_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize">{status.replace('_', ' ')}</span>
                  <Badge variant="outline">{formatNumber(count)}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500">
        <Clock className="h-4 w-4 inline mr-1" />
        Last updated: {new Date(dashboardData.generated_at).toLocaleString()}
      </div>
    </div>
  );
};

export default EmailStatisticsDashboard;
