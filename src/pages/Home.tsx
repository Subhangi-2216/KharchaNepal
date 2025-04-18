import { useState } from "react";
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

const ExpenseChart = () => (
  <div className="w-full h-[300px] bg-muted/50 rounded-lg flex items-center justify-center">
    <div className="text-center p-6">
      <h3 className="text-lg font-medium">Expense Chart Visualization</h3>
      <p className="text-sm text-muted-foreground mt-1">
        Chart showing expenses by category for the past 30 days
      </p>
      <div className="mt-6 space-y-2">
        <div className="flex items-center">
          <div className="w-48 h-4 bg-primary rounded-full"></div>
          <span className="ml-2 text-sm">Food (35%)</span>
        </div>
        <div className="flex items-center">
          <div className="w-28 h-4 bg-accent rounded-full"></div>
          <span className="ml-2 text-sm">Travel (20%)</span>
        </div>
        <div className="flex items-center">
          <div className="w-24 h-4 bg-blue-400 rounded-full"></div>
          <span className="ml-2 text-sm">Entertainment (15%)</span>
        </div>
        <div className="flex items-center">
          <div className="w-32 h-4 bg-orange-400 rounded-full"></div>
          <span className="ml-2 text-sm">Household Bill (25%)</span>
        </div>
        <div className="flex items-center">
          <div className="w-8 h-4 bg-gray-400 rounded-full"></div>
          <span className="ml-2 text-sm">Other (5%)</span>
        </div>
      </div>
    </div>
  </div>
);

const SupportChatbot = () => {
  const [messages, setMessages] = useState([
    { role: "system", content: "Hello! I'm your support assistant. How can I help you with the expense tracker today?" }
  ]);
  const [input, setInput] = useState("");

  const handleSendMessage = () => {
    if (!input.trim()) return;
    
    setMessages([...messages, { role: "user", content: input }]);
    
    setTimeout(() => {
      let botResponse = "I don't have an answer for that yet.";
      
      if (input.toLowerCase().includes("category")) {
        botResponse = "You can categorize expenses as Food, Travel, Entertainment, Household Bill, or Other. To change a category, edit the expense and select a new category from the dropdown.";
      } else if (input.toLowerCase().includes("receipt") || input.toLowerCase().includes("scan")) {
        botResponse = "To scan a receipt, go to the Expenses page, click 'Add New Expense' and choose 'Scan Receipt'. You can then upload an image of your receipt.";
      } else if (input.toLowerCase().includes("report")) {
        botResponse = "You can generate reports from the Reports page. Select a date range, choose categories to include, and click 'Generate Report'.";
      }
      
      setMessages(prev => [...prev, { role: "system", content: botResponse }]);
    }, 500);
    
    setInput("");
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
          </div>
          <div className="p-4 border-t flex">
            <Input 
              placeholder="Type your question..." 
              className="flex-1" 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSendMessage()}
            />
            <Button 
              className="ml-2" 
              size="icon"
              onClick={handleSendMessage}
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const SummaryCard = ({ title, value, description }: { title: string; value: string; description?: string }) => (
  <Card>
    <CardHeader className="pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">NPR {value}</div>
      {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
    </CardContent>
  </Card>
);

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your expenses and insights
        </p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard 
          title="Monthly Total" 
          value="24,560" 
        />
        <SummaryCard 
          title="Largest Expense" 
          value="4,500" 
          description="Household Bill - Electricity"
        />
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Expense Summary</CardTitle>
            <CardDescription>Your expense breakdown for the past 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="chart">
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="chart">Chart</TabsTrigger>
                <TabsTrigger value="categories">By Category</TabsTrigger>
              </TabsList>
              <TabsContent value="chart">
                <ExpenseChart />
              </TabsContent>
              <TabsContent value="categories">
                <div className="space-y-4">
                  {[
                    { name: "Food", amount: 8596, percentage: 35 },
                    { name: "Travel", amount: 4912, percentage: 20 },
                    { name: "Entertainment", amount: 3684, percentage: 15 },
                    { name: "Household Bill", amount: 6140, percentage: 25 },
                    { name: "Other", amount: 1228, percentage: 5 }
                  ].map((category) => (
                    <div key={category.name} className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">{category.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {category.percentage}% of total
                        </div>
                      </div>
                      <div className="font-medium">NPR {category.amount.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        <SupportChatbot />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Recent Expenses</h2>
          <p className="text-sm text-muted-foreground">Your latest transactions</p>
        </div>
        <Button variant="outline" size="sm">
          View All <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden">
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
            {[
              { merchant: "Bhatbhateni", date: "Apr 15, 2025", category: "Food", amount: 1850 },
              { merchant: "City Taxi", date: "Apr 14, 2025", category: "Travel", amount: 350 },
              { merchant: "Nepal Electricity", date: "Apr 13, 2025", category: "Household Bill", amount: 4500 },
              { merchant: "QFX Cinemas", date: "Apr 11, 2025", category: "Entertainment", amount: 800 },
              { merchant: "Daraz", date: "Apr 10, 2025", category: "Other", amount: 1200 }
            ].map((expense, idx) => (
              <tr key={idx} className="hover:bg-muted/30">
                <td className="p-3">{expense.merchant}</td>
                <td className="p-3 text-muted-foreground">{expense.date}</td>
                <td className="p-3">
                  <span className="px-2 py-1 rounded-full text-xs bg-muted">{expense.category}</span>
                </td>
                <td className="p-3 text-right font-medium">NPR {expense.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
