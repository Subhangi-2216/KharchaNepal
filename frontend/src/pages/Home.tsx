import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowRight, Send } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { format, parseISO } from 'date-fns';
import { Link } from 'react-router-dom';

interface LargestExpenseDetail {
  amount: number;
  category?: string | null;
  merchant_name?: string | null;
}

interface DashboardStatsData {
  monthly_total: number;
  largest_expense?: LargestExpenseDetail | null;
}

interface CategorySummaryItem {
  category: string;
  total_amount: number;
  percentage: number;
}

interface DashboardSummaryData {
  summary: CategorySummaryItem[];
  total_last_30_days: number;
}

interface Expense {
    id: number;
    merchant_name?: string | null;
    date: string;
    amount: number;
    currency: string;
    category?: { value: string } | string | null;
}

// --- Type Definition for Chat Messages ---
interface ChatMessage {
  role: "system" | "user";
  content: string;
}

const DynamicExpenseChart = ({ summaryData }: { summaryData: CategorySummaryItem[] }) => {
  const colors = [
    "bg-primary",
    "bg-teal-400",
    "bg-indigo-400",
    "bg-orange-400",
    "bg-rose-400",
    "bg-cyan-400",
    "bg-lime-400",
    "bg-gray-400"
  ];

  const getCategoryColor = (category: string, index: number): string => {
    const lowerCaseCat = category.toLowerCase();
    if (lowerCaseCat.includes("food")) return colors[0];
    if (lowerCaseCat.includes("travel")) return colors[1];
    if (lowerCaseCat.includes("entertainment")) return colors[2];
    if (lowerCaseCat.includes("household")) return colors[3];
    if (lowerCaseCat.includes("other")) return colors[6];
    if (lowerCaseCat.includes("uncategorized")) return colors[7];
    return colors[index % colors.length];
  };

  if (!summaryData || summaryData.length === 0) {
     return (
       <div className="w-full h-[300px] bg-muted/50 rounded-lg flex items-center justify-center p-6">
         <p className="text-sm text-muted-foreground">No expense data available for the chart.</p>
       </div>
     );
   }

  return (
    <div className="w-full h-auto min-h-[300px] bg-muted/50 rounded-lg p-6">
      <h3 className="text-lg font-medium text-center mb-2">Expense Chart Visualization</h3>
      <p className="text-sm text-muted-foreground text-center mt-1 mb-6">
        Expenses by category for the past 30 days
      </p>
      <div className="space-y-3">
        {summaryData.map((item, index) => (
          <div key={item.category || `cat-${index}`} className="flex items-center">
            <div className="w-1/3 pr-2">
                <div className="text-sm truncate text-right">{item.category} ({item.percentage.toFixed(1)}%)</div>
            </div>
            <div className="w-2/3">
                <div
                    className={`h-4 rounded-full ${getCategoryColor(item.category, index)}`}
                    style={{ width: `${item.percentage}%` }}
                    title={`NPR ${item.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SupportChatbot = () => {
  const { token } = useAuth();
  // Use the ChatMessage interface for the state type
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "system", content: "Hey, I'm a Support Assistant here to help you navigate the application or access certain features of the app." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    const userQuery = input.trim();
    if (!userQuery || isLoading) return;

    // Explicitly type the new user message
    const newUserMessage: ChatMessage = { role: "user", content: userQuery };
    setMessages(prev => [...prev, newUserMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '/api/chatbot/support';

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ query: userQuery })
      });

      if (!response.ok) {
         const errorData = await response.json().catch(() => ({ detail: 'Unknown error from chatbot API' }));
         throw new Error(errorData.detail || `Error: ${response.status}`);
      }

      const botResponseData = await response.json();

      // Explicitly type the new system message
      const newSystemMessage: ChatMessage = { role: "system", content: botResponseData.data };
      setMessages(prev => [...prev, newSystemMessage]);

    } catch (error: any) {
        console.error("Support Chatbot Error:", error);
        toast.error(`Chatbot error: ${error.message}`);
        // Explicitly type the error message
        const errorSystemMessage: ChatMessage = { role: "system", content: "Sorry, I encountered an error. Please try again." };
        setMessages(prev => [...prev, errorSystemMessage]);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Support Assistant</CardTitle>
        <CardDescription>Ask questions about using the expense tracker</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[400px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div 
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === "user" 
                      ? "bg-primary text-primary-foreground" 
                      : "bg-muted"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
                 <div className="flex justify-start">
                     <div className="max-w-[80%] rounded-lg px-4 py-2 bg-muted animate-pulse">...</div>
                 </div>
            )}
          </div>
          <div className="p-4 border-t flex">
            <Input 
              placeholder="Type your question..." 
              className="flex-1" 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !isLoading && handleSendMessage()}
              disabled={isLoading}
            />
            <Button 
              className="ml-2" 
              size="icon"
              onClick={handleSendMessage}
              disabled={isLoading}
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const SummaryCard = ({ title, value, description, isLoading }: {
    title: string;
    value: string | number | undefined | null;
    description?: string | null;
    isLoading: boolean;
}) => (
  <Card>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <>
          <Skeleton className="h-8 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </>
      ) : (
        <>
          <div className="text-2xl font-bold">
            {typeof value === 'number'
              ? `NPR ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              : (value || 'N/A')}
          </div>
          {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
        </>
      )}
    </CardContent>
  </Card>
);

export default function HomePage() {
  const { token, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [statsData, setStatsData] = useState<DashboardStatsData | null>(null);
  const [summaryData, setSummaryData] = useState<DashboardSummaryData | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthLoading && isAuthenticated && token) {
      const fetchData = async () => {
        setIsLoading(true);
        setError(null);
        setStatsData(null);
        setSummaryData(null);
        setRecentExpenses(null);
        console.log("HomePage: Fetching all dashboard data...");

        const headers = { 'Authorization': `Bearer ${token}` };
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const statsUrl = `${baseUrl}/api/dashboard/stats`;
        const summaryUrl = `${baseUrl}/api/dashboard/summary`;
        const recentExpensesUrl = `${baseUrl}/api/expenses?limit=5&skip=0`;

        try {
          const [statsResponse, summaryResponse, recentExpensesResponse] = await Promise.all([
            fetch(statsUrl, { headers }),
            fetch(summaryUrl, { headers }),
            fetch(recentExpensesUrl, { headers })
          ]);

          let fetchedStatsData: DashboardStatsData | null = null;
          if (statsResponse.ok) {
            fetchedStatsData = await statsResponse.json();
          } else {
            const statsErrorText = await statsResponse.text();
            console.error("Stats Fetch Error:", statsResponse.status, statsErrorText);
            throw new Error(`Failed to fetch stats (${statsResponse.status})`);
          }

          let fetchedSummaryData: DashboardSummaryData | null = null;
          if (summaryResponse.ok) {
            fetchedSummaryData = await summaryResponse.json();
          } else {
            const summaryErrorText = await summaryResponse.text();
            console.error("Summary Fetch Error:", summaryResponse.status, summaryErrorText);
            throw new Error(`Failed to fetch summary (${summaryResponse.status})`);
          }

          let fetchedRecentExpenses: Expense[] | null = null;
          if (recentExpensesResponse.ok) {
            fetchedRecentExpenses = await recentExpensesResponse.json();
          } else {
             const recentErrorText = await recentExpensesResponse.text();
             console.error("Recent Expenses Fetch Error:", recentExpensesResponse.status, recentErrorText);
             throw new Error(`Failed to fetch recent expenses (${recentExpensesResponse.status})`);
          }

          console.log("HomePage: Data fetched successfully", { fetchedStatsData, fetchedSummaryData, fetchedRecentExpenses });
          setStatsData(fetchedStatsData);
          setSummaryData(fetchedSummaryData);
          setRecentExpenses(fetchedRecentExpenses);

        } catch (err: any) {
          console.error("HomePage: Fetch error:", err);
          const errorMsg = err.message || "Failed to load dashboard data.";
          setError(errorMsg);
          toast.error(errorMsg);
          setStatsData(null);
          setSummaryData(null);
          setRecentExpenses(null);
        } finally {
          setIsLoading(false);
        }
      };
      fetchData();
    } else if (!isAuthLoading && !isAuthenticated) {
      setIsLoading(false);
      setError("Please log in to view the dashboard.");
      setStatsData(null);
      setSummaryData(null);
      setRecentExpenses(null);
    } else {
       setIsLoading(true);
    }
  }, [isAuthenticated, token, isAuthLoading]);

  const largestExpenseDescription = statsData?.largest_expense
    ? `${statsData.largest_expense.category || 'N/A'} - ${statsData.largest_expense.merchant_name || 'N/A'}`
    : (statsData === null ? null : 'No expenses this month');

  const showOverallLoading = isAuthLoading || isLoading;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your expenses and insights
        </p>
      </div>
      
      {error && !showOverallLoading && (
         <Card className="bg-destructive/10 border-destructive">
             <CardHeader>
                 <CardTitle className="text-destructive">Error Loading Dashboard</CardTitle>
                 <CardDescription className="text-destructive">{error}</CardDescription>
             </CardHeader>
         </Card>
       )}

      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard 
          title="Monthly Total" 
          value={statsData?.monthly_total}
          isLoading={showOverallLoading}
        />
        <SummaryCard 
          title="Largest Expense (Current Month)" 
          value={statsData?.largest_expense?.amount}
          description={largestExpenseDescription}
          isLoading={showOverallLoading}
        />
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Expense Summary</CardTitle>
            <CardDescription>Your expense breakdown for the past 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            {showOverallLoading ? (
                <Skeleton className="h-[400px] w-full" />
            ) : summaryData && summaryData.summary.length > 0 ? (
                <Tabs defaultValue="chart">
                  <TabsList className="grid w-full grid-cols-2 mb-4">
                    <TabsTrigger value="chart">Chart</TabsTrigger>
                    <TabsTrigger value="categories">By Category</TabsTrigger>
                  </TabsList>
                  <TabsContent value="chart">
                    <DynamicExpenseChart summaryData={summaryData.summary} />
                  </TabsContent>
                  <TabsContent value="categories">
                    <div className="space-y-4">
                      {summaryData.summary.map((item, index) => (
                        <div key={item.category || `cat-${index}`} className="flex justify-between items-center">
                          <div>
                            <div className="font-medium">{item.category}</div>
                            <div className="text-sm text-muted-foreground">
                              {item.percentage.toFixed(1)}% of total (Last 30d)
                            </div>
                          </div>
                          <div className="font-medium">
                              NPR {item.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        </div>
                      ))}
                       <div className="flex justify-between items-center border-t pt-4 mt-4">
                          <div className="font-bold">Total (Last 30d)</div>
                          <div className="font-bold">
                              NPR {summaryData.total_last_30_days.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
            ) : (
                <div className="text-center p-10 text-muted-foreground h-[400px] flex items-center justify-center">
                  No expense data found for the last 30 days.
                </div>
            )}
          </CardContent>
        </Card>
        <SupportChatbot />
      </div>

      <div className="flex items-center justify-between mt-6">
        <div>
          <h2 className="text-xl font-semibold">Recent Expenses</h2>
          <p className="text-sm text-muted-foreground">Your latest 5 transactions</p>
        </div>
        <Link to="/expenses">
            <Button variant="outline" size="sm">
              View All <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
        </Link>
      </div>

      <Card>
          <CardContent className="p-0">
              <div className="border-0 rounded-lg overflow-hidden">
                  <table className="w-full">
                  <thead className="bg-muted/50">
                      <tr>
                      <th className="text-left p-3 font-medium text-sm">Merchant</th>
                      <th className="text-left p-3 font-medium text-sm">Date</th>
                      <th className="text-left p-3 font-medium text-sm">Category</th>
                      <th className="text-right p-3 font-medium text-sm">Amount</th>
                      </tr>
                  </thead>
                  <tbody className="divide-y">
                      {showOverallLoading ? (
                          Array.from({ length: 5 }).map((_, idx) => (
                              <tr key={`skel-${idx}`}>
                                  <td className="p-3"><Skeleton className="h-5 w-3/4" /></td>
                                  <td className="p-3"><Skeleton className="h-5 w-1/2" /></td>
                                  <td className="p-3"><Skeleton className="h-5 w-2/4" /></td>
                                  <td className="p-3 text-right"><Skeleton className="h-5 w-1/4 ml-auto" /></td>
                              </tr>
                          ))
                      ) : recentExpenses && recentExpenses.length > 0 ? (
                          recentExpenses.map((expense) => (
                          <tr key={expense.id} className="hover:bg-muted/30">
                              <td className="p-3">{expense.merchant_name || 'N/A'}</td>
                              <td className="p-3 text-muted-foreground">
                                  {format(parseISO(expense.date), "MMM d, yyyy")}
                              </td>
                              <td className="p-3">
                              <span className="px-2 py-1 rounded-full text-xs bg-muted">
                                  {typeof expense.category === 'string' ? expense.category :
                                  expense.category?.value ? expense.category.value : 'N/A'}
                              </span>
                              </td>
                              <td className="p-3 text-right font-medium">
                                  {expense.currency} {expense.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </td>
                          </tr>
                          ))
                      ) : (
                          <tr>
                              <td colSpan={4} className="text-center p-10 text-muted-foreground">
                                  No recent expenses found.
                              </td>
                          </tr>
                      )}
                  </tbody>
                  </table>
              </div>
          </CardContent>
      </Card>
    </div>
  );
}
