
import { useState } from "react";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent 
} from "@/components/ui/card";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { 
  CalendarIcon, 
  ChevronDown,
  ChevronUp,
  Download, 
  Edit, 
  FileText, 
  MessageSquare,
  Plus, 
  Search, 
  Send, 
  Trash, 
  Upload 
} from "lucide-react";

const mockExpenses = [
  { id: 1, merchant: "Bhatbhateni", date: "2025-04-15", category: "Food", amount: 1850 },
  { id: 2, merchant: "City Taxi", date: "2025-04-14", category: "Travel", amount: 350 },
  { id: 3, merchant: "Nepal Electricity", date: "2025-04-13", category: "Household Bill", amount: 4500 },
  { id: 4, merchant: "QFX Cinemas", date: "2025-04-11", category: "Entertainment", amount: 800 },
  { id: 5, merchant: "Daraz", date: "2025-04-10", category: "Other", amount: 1200 },
  { id: 6, merchant: "Fuel Station", date: "2025-04-09", category: "Travel", amount: 2000 },
  { id: 7, merchant: "Restaurant", date: "2025-04-08", category: "Food", amount: 1650 },
  { id: 8, merchant: "Internet Bill", date: "2025-04-07", category: "Household Bill", amount: 1200 },
  { id: 9, merchant: "Clothing Store", date: "2025-04-05", category: "Other", amount: 3500 },
  { id: 10, merchant: "Movie Tickets", date: "2025-04-03", category: "Entertainment", amount: 900 }
];

function ExpenseQueryChatbot() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { role: "system", content: "Hello! I'm your Expense Query Assistant. Ask me about your expenses or tell me to add a new one." }
  ]);
  const [input, setInput] = useState("");

  const handleSendMessage = () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: "user", content: input }]);
    
    setTimeout(() => {
      let botResponse = "I'm not sure how to answer that query.";
      if (input.toLowerCase().includes("how much") && input.toLowerCase().includes("food")) {
        botResponse = "You spent NPR 3,500 on Food this month.";
      } else if (input.toLowerCase().includes("travel") && input.toLowerCase().includes("last week")) {
        botResponse = "Your Travel expenses last week were NPR 2,350.";
      } else if (input.toLowerCase().includes("add") && input.toLowerCase().includes("expense")) {
        botResponse = "I've added a new expense of NPR 500 for Food at Bhatbhateni on April 15th, 2025.";
      }
      setMessages(prev => [...prev, { role: "system", content: botResponse }]);
    }, 500);
    
    setInput("");
  };

  return (
    <div 
      className={cn(
        "fixed transition-all duration-300 z-50",
        isExpanded 
          ? "bottom-4 right-4 w-full md:w-1/3 h-[calc(100vh-6rem)]" 
          : "bottom-4 right-4 w-14 h-14"
      )}
    >
      {isExpanded ? (
        <Card className="h-full flex flex-col">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <div>
              <CardTitle>Expense Query Assistant</CardTitle>
              <CardDescription>Ask about your expenses or add new ones</CardDescription>
            </div>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => setIsExpanded(false)}
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === "user" 
                        ? "bg-primary text-primary-foreground" 
                        : "bg-muted"
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t flex">
                <Input 
                  placeholder="Ask about your expenses..." 
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
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Button 
          className="w-full h-full rounded-full"
          variant="default"
          onClick={() => setIsExpanded(true)}
        >
          <MessageSquare className="h-6 w-6" />
        </Button>
      )}
    </div>
  );
}

function AddExpenseDialog() {
  const [date, setDate] = useState<Date | undefined>(new Date());
  
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add New Expense
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <Tabs defaultValue="manual">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="manual">Manual Entry</TabsTrigger>
            <TabsTrigger value="scan">Scan Receipt</TabsTrigger>
          </TabsList>
          
          <TabsContent value="manual">
            <DialogHeader>
              <DialogTitle>Add New Expense</DialogTitle>
              <DialogDescription>
                Enter the details of your expense
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="merchant" className="text-right">
                  Merchant
                </Label>
                <Input id="merchant" placeholder="Merchant name" className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="date" className="text-right">
                  Date
                </Label>
                <div className="col-span-3">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !date && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP") : <span>Pick a date</span>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={date}
                        onSelect={setDate}
                        initialFocus
                        className={cn("p-3 pointer-events-auto")}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="amount" className="text-right">
                  Amount (NPR)
                </Label>
                <Input 
                  id="amount" 
                  placeholder="0.00" 
                  className="col-span-3"
                  type="number"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="category" className="text-right">
                  Category
                </Label>
                <Select>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="food">Food</SelectItem>
                    <SelectItem value="travel">Travel</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="household_bill">Household Bill</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="scan">
            <DialogHeader>
              <DialogTitle>Scan Receipt</DialogTitle>
              <DialogDescription>
                Upload a photo of your receipt for OCR processing
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-muted/30">
                <div className="mx-auto flex flex-col items-center">
                  <Upload className="h-10 w-10 text-muted-foreground mb-2" />
                  <p className="text-sm font-medium mb-1">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-muted-foreground">
                    JPG, PNG or PDF (max. 10MB)
                  </p>
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                After uploading, we'll extract the information using OCR technology.
                You'll be able to review and edit before saving.
              </div>
              <div className="hidden border rounded-lg p-4 mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Extracted Information</span>
                  <span className="text-xs text-muted-foreground">Edit if needed</span>
                </div>
                <div className="grid gap-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Merchant:</span>
                    <span className="font-medium">Bhatbhateni</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Date:</span>
                    <span className="font-medium">April 15, 2025</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total:</span>
                    <span className="font-medium">NPR 1,850.00</span>
                  </div>
                  <div className="mt-2">
                    <Label htmlFor="scan-category" className="text-sm mb-1 block">
                      Select Category
                    </Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="food">Food</SelectItem>
                        <SelectItem value="travel">Travel</SelectItem>
                        <SelectItem value="entertainment">Entertainment</SelectItem>
                        <SelectItem value="household_bill">Household Bill</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
        
        <DialogFooter>
          <Button type="submit">Save Expense</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function ExpensesPage() {
  const [filterText, setFilterText] = useState("");
  
  const filteredExpenses = mockExpenses.filter(expense => 
    expense.merchant.toLowerCase().includes(filterText.toLowerCase()) ||
    expense.category.toLowerCase().includes(filterText.toLowerCase())
  );
  
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Expenses</h1>
          <p className="text-muted-foreground">
            Manage and view your expenses
          </p>
        </div>
        <AddExpenseDialog />
      </div>
      
      <div className="w-full">
        <div className="flex items-center space-x-2 mb-4">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search expenses..." 
            value={filterText}
            onChange={e => setFilterText(e.target.value)}
            className="flex-1"
          />
        </div>
        
        <div className="border rounded-lg overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium text-sm">Merchant</th>
                <th className="text-left p-3 font-medium text-sm">Date</th>
                <th className="text-left p-3 font-medium text-sm">Category</th>
                <th className="text-right p-3 font-medium text-sm">Amount</th>
                <th className="text-right p-3 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredExpenses.map(expense => (
                <tr key={expense.id} className="hover:bg-muted/30">
                  <td className="p-3">{expense.merchant}</td>
                  <td className="p-3 text-muted-foreground">
                    {format(new Date(expense.date), "MMM dd, yyyy")}
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-1 rounded-full text-xs bg-muted">
                      {expense.category}
                    </span>
                  </td>
                  <td className="p-3 text-right font-medium">NPR {expense.amount}</td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end space-x-2">
                      <Button variant="ghost" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredExpenses.length === 0 && (
          <div className="text-center p-8 border rounded-lg bg-muted/30 mt-4">
            <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
            <h3 className="font-medium">No expenses found</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Try adjusting your search or add a new expense
            </p>
          </div>
        )}
      </div>

      <ExpenseQueryChatbot />
    </div>
  );
}
