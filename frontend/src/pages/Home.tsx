import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Send,
  PieChart,
  TrendingUp,
  CreditCard,
  Calendar,
  BarChart4,
  Plus
} from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { format, parseISO } from 'date-fns';
import { Link } from 'react-router-dom';
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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
    "bg-primary/90 hover:bg-primary",
    "bg-teal-500/90 hover:bg-teal-500",
    "bg-indigo-500/90 hover:bg-indigo-500",
    "bg-orange-500/90 hover:bg-orange-500",
    "bg-rose-500/90 hover:bg-rose-500",
    "bg-cyan-500/90 hover:bg-cyan-500",
    "bg-lime-500/90 hover:bg-lime-500",
    "bg-gray-500/90 hover:bg-gray-500"
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
      <div className="w-full h-[300px] rounded-lg flex flex-col items-center justify-center p-6 border border-dashed border-muted-foreground/20">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <PieChart className="h-8 w-8 text-muted-foreground/50" />
        </div>
        <p className="text-sm text-muted-foreground">No expense data available for the chart.</p>
        <p className="text-xs text-muted-foreground/70 mt-1">Add some expenses to see your spending breakdown.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-auto min-h-[300px] rounded-lg p-6">
      <div className="space-y-4">
        {summaryData.map((item, index) => (
          <div key={item.category || `cat-${index}`} className="group">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full ${getCategoryColor(item.category, index).split(' ')[0]} mr-2`}></div>
                <span className="text-sm font-medium">{item.category}</span>
              </div>
              <div className="text-sm font-medium">
                {item.percentage.toFixed(1)}%
              </div>
            </div>
            <div className="relative h-2 w-full bg-muted rounded-full overflow-hidden">
              <div
                className={`absolute top-0 left-0 h-full rounded-full transition-all ${getCategoryColor(item.category, index)}`}
                style={{ width: `${Math.max(item.percentage, 3)}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-xs text-muted-foreground">
                {item.total_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} NPR
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SupportChatbot = () => {
  const { token } = useAuth();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "system", content: "👋 Hi there! I'm your KharchaNP Assistant. I can help you navigate the app, understand features, or answer questions about expense tracking. What can I help you with today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Scroll to bottom of messages when new ones are added, but only within the chat container
  useEffect(() => {
    if (messagesEndRef.current) {
      // Use the parent container's scrollTop instead of scrollIntoView
      const chatContainer = messagesEndRef.current.parentElement;
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = async () => {
    const userQuery = input.trim();
    if (!userQuery || isLoading) return;

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
      const newSystemMessage: ChatMessage = { role: "system", content: botResponseData.data };

      // Add a small delay to make the response feel more natural
      setTimeout(() => {
        setMessages(prev => [...prev, newSystemMessage]);
        setIsLoading(false);
      }, 500);

    } catch (error: any) {
        console.error("Support Chatbot Error:", error);
        toast.error(`Chatbot error: ${error.message}`);
        const errorSystemMessage: ChatMessage = {
          role: "system",
          content: "Sorry, I encountered an error processing your request. Please try again or contact support if the issue persists."
        };
        setMessages(prev => [...prev, errorSystemMessage]);
        setIsLoading(false);
    }
  };

  // Suggested questions for quick access
  const suggestedQuestions = [
    "How do I add an expense?",
    "How does OCR work?",
    "Can I export my data?",
    "How to view reports?"
  ];

  return (
    <Card className="h-full border-border/40 hover:border-border/80 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Support Assistant</CardTitle>
            <CardDescription>Ask questions about using the expense tracker</CardDescription>
          </div>
          <div className="bg-primary/10 text-primary p-2 rounded-full">
            <Send className="h-4 w-4" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[400px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "system" && (
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center mr-2">
                    <Send className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/50 border border-border/40"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center mr-2">
                  <Send className="h-4 w-4 text-primary" />
                </div>
                <div className="max-w-[80%] rounded-lg px-4 py-3 bg-muted/50 border border-border/40">
                  <div className="flex space-x-2">
                    <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="h-2 w-2 rounded-full bg-muted-foreground/30 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length === 1 && !isLoading && (
            <div className="px-4 pb-2">
              <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((question, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => {
                      setInput(question);
                      setTimeout(() => handleSendMessage(), 100);
                    }}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          )}

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

const SummaryCard = ({
  title,
  value,
  description,
  isLoading,
  icon: Icon = TrendingUp,
  trend,
  trendValue
}: {
  title: string;
  value: string | number | undefined | null;
  description?: string | null;
  isLoading: boolean;
  icon?: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}) => (
  <Card className="overflow-hidden border-border/40 hover:border-border/80 transition-colors">
    <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      <div className={cn(
        "p-2 rounded-full",
        trend === 'up' ? "bg-green-100 text-green-700" :
        trend === 'down' ? "bg-red-100 text-red-700" :
        "bg-primary/10 text-primary"
      )}>
        <Icon className="h-4 w-4" />
      </div>
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <>
          <Skeleton className="h-9 w-3/4 mb-2" />
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

          {trend && trendValue && (
            <div className="flex items-center mt-2">
              <Badge variant={trend === 'up' ? "success" : trend === 'down' ? "destructive" : "outline"} className="text-xs">
                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
              </Badge>
            </div>
          )}
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
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your expenses and insights
          </p>
        </div>
        <Link to="/expenses">
          <Button className="w-full sm:w-auto">
            <Plus className="mr-2 h-4 w-4" /> Add New Expense
          </Button>
        </Link>
      </div>

      {error && !showOverallLoading && (
        <Card className="bg-destructive/10 border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Dashboard</CardTitle>
            <CardDescription className="text-destructive">{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Monthly Total"
          value={statsData?.monthly_total}
          isLoading={showOverallLoading}
          icon={CreditCard}
          trend="up"
          trendValue="12% from last month"
        />
        <SummaryCard
          title="Largest Expense"
          value={statsData?.largest_expense?.amount}
          description={largestExpenseDescription}
          isLoading={showOverallLoading}
          icon={BarChart4}
        />
        <SummaryCard
          title="Total Categories"
          value={summaryData?.summary.length || 0}
          isLoading={showOverallLoading}
          icon={PieChart}
        />
        <SummaryCard
          title="Last 30 Days"
          value={summaryData?.total_last_30_days || 0}
          isLoading={showOverallLoading}
          icon={Calendar}
          trend="down"
          trendValue="8% from previous period"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-border/40 hover:border-border/80 transition-colors">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Expense Summary</CardTitle>
                <CardDescription>Your expense breakdown for the past 30 days</CardDescription>
              </div>
              <div className="bg-primary/10 text-primary p-2 rounded-full">
                <PieChart className="h-4 w-4" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="pb-2">
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
                            {item.percentage.toFixed(1)}% of total
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
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <PieChart className="h-8 w-8 text-muted-foreground/50" />
                  </div>
                  <p className="text-sm font-medium">No expense data found</p>
                  <p className="text-xs text-muted-foreground mt-1">Add some expenses to see your spending breakdown</p>
                  <Button variant="outline" size="sm" className="mt-4">
                    <Plus className="mr-2 h-3 w-3" /> Add Expense
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="pt-0">
            <Link to="/reports" className="text-xs text-primary hover:underline w-full text-center">
              View detailed reports →
            </Link>
          </CardFooter>
        </Card>
        <SupportChatbot />
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
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

      <Card className="border-border/40 hover:border-border/80 transition-colors overflow-hidden">
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-3 font-medium text-sm">Merchant</th>
                  <th className="text-left p-3 font-medium text-sm hidden md:table-cell">Date</th>
                  <th className="text-left p-3 font-medium text-sm">Category</th>
                  <th className="text-right p-3 font-medium text-sm">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {showOverallLoading ? (
                  Array.from({ length: 5 }).map((_, idx) => (
                    <tr key={`skel-${idx}`}>
                      <td className="p-3"><Skeleton className="h-5 w-3/4" /></td>
                      <td className="p-3 hidden md:table-cell"><Skeleton className="h-5 w-1/2" /></td>
                      <td className="p-3"><Skeleton className="h-5 w-2/4" /></td>
                      <td className="p-3 text-right"><Skeleton className="h-5 w-1/4 ml-auto" /></td>
                    </tr>
                  ))
                ) : recentExpenses && recentExpenses.length > 0 ? (
                  recentExpenses.map((expense) => (
                    <tr key={expense.id} className="hover:bg-muted/30">
                      <td className="p-3 font-medium">{expense.merchant_name || 'N/A'}</td>
                      <td className="p-3 text-muted-foreground hidden md:table-cell">
                        {format(parseISO(expense.date), "MMM d, yyyy")}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline" className="font-normal">
                          {typeof expense.category === 'string' ? expense.category :
                            expense.category?.value ? expense.category.value : 'N/A'}
                        </Badge>
                      </td>
                      <td className="p-3 text-right font-medium">
                        {expense.currency} {expense.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center p-10 text-muted-foreground">
                      <div className="flex flex-col items-center py-8">
                        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                          <CreditCard className="h-6 w-6 text-muted-foreground/50" />
                        </div>
                        <p className="text-sm font-medium">No recent expenses found</p>
                        <p className="text-xs text-muted-foreground mt-1">Add your first expense to get started</p>
                        <Link to="/expenses">
                          <Button variant="outline" size="sm" className="mt-4">
                            <Plus className="mr-2 h-3 w-3" /> Add Expense
                          </Button>
                        </Link>
                      </div>
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
