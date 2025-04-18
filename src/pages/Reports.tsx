
import { useState } from "react";
import { format } from "date-fns";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  Checkbox
} from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { CalendarIcon, Download, FileText } from "lucide-react";

// Mock report data
const reportData = [
  { category: "Food", amount: 12500 },
  { category: "Travel", amount: 6800 },
  { category: "Entertainment", amount: 4200 },
  { category: "Household Bill", amount: 15300 },
  { category: "Other", amount: 3400 }
];

// Report chart component
const ReportChart = () => (
  <div className="w-full h-[300px] bg-muted/50 rounded-lg flex items-center justify-center">
    <div className="text-center p-6">
      <h3 className="text-lg font-medium">Report Visualization</h3>
      <p className="text-sm text-muted-foreground mt-1">
        Chart showing expenses by selected categories and date range
      </p>
      <div className="mt-6 space-y-2">
        {reportData.map(item => (
          <div key={item.category} className="flex items-center">
            <div 
              className={`h-4 rounded-full ${
                item.category === "Food" ? "bg-primary" :
                item.category === "Travel" ? "bg-accent" :
                item.category === "Entertainment" ? "bg-blue-400" :
                item.category === "Household Bill" ? "bg-orange-400" :
                "bg-gray-400"
              }`}
              style={{ width: `${(item.amount / 42200) * 100}%` }}
            ></div>
            <span className="ml-2 text-sm">
              {item.category} (NPR {item.amount.toLocaleString()})
            </span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default function ReportsPage() {
  const [startDate, setStartDate] = useState<Date | undefined>(new Date(2025, 3, 1)); // April 1, 2025
  const [endDate, setEndDate] = useState<Date | undefined>(new Date(2025, 3, 15)); // April 15, 2025
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]); 
  const [reportGenerated, setReportGenerated] = useState(false);
  
  const handleGenerateReport = () => {
    setReportGenerated(true);
  };
  
  const handleCategoryChange = (category: string) => {
    setSelectedCategories(current => 
      current.includes(category) 
        ? current.filter(c => c !== category)
        : [...current, category]
    );
  };
  
  const allCategories = ["Food", "Travel", "Entertainment", "Household Bill", "Other"];
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
        <p className="text-muted-foreground">
          Generate and download expense reports
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Report Filter</CardTitle>
          <CardDescription>
            Set date range and categories to include in your report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !startDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={setStartDate}
                    initialFocus
                    className={cn("p-3 pointer-events-auto")}
                  />
                </PopoverContent>
              </Popover>
            </div>
            
            <div className="space-y-2">
              <Label>End Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !endDate && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={setEndDate}
                    initialFocus
                    className={cn("p-3 pointer-events-auto")}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label>Categories</Label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {allCategories.map(category => (
                <div key={category} className="flex items-center space-x-2">
                  <Checkbox 
                    id={`category-${category}`} 
                    checked={selectedCategories.includes(category)}
                    onCheckedChange={() => handleCategoryChange(category)}
                  />
                  <Label htmlFor={`category-${category}`} className="text-sm">
                    {category}
                  </Label>
                </div>
              ))}
            </div>
          </div>
          
          <div className="pt-4">
            <Button onClick={handleGenerateReport}>Generate Report</Button>
          </div>
        </CardContent>
      </Card>
      
      {reportGenerated && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>Expense Report</CardTitle>
                <CardDescription>
                  {startDate && endDate ? (
                    <>
                      {format(startDate, "MMMM d, yyyy")} to {format(endDate, "MMMM d, yyyy")}
                    </>
                  ) : "Custom Date Range"}
                </CardDescription>
              </div>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download (.xlsx)
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ReportChart />
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-3">Summary</h3>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-3 font-medium text-sm">Category</th>
                      <th className="text-right p-3 font-medium text-sm">Amount (NPR)</th>
                      <th className="text-right p-3 font-medium text-sm">Percentage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {reportData.map(item => (
                      <tr key={item.category}>
                        <td className="p-3">{item.category}</td>
                        <td className="p-3 text-right font-medium">{item.amount.toLocaleString()}</td>
                        <td className="p-3 text-right">
                          {Math.round((item.amount / 42200) * 100)}%
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-muted/30">
                      <td className="p-3 font-medium">Total</td>
                      <td className="p-3 text-right font-medium">
                        {reportData.reduce((sum, item) => sum + item.amount, 0).toLocaleString()}
                      </td>
                      <td className="p-3 text-right">100%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
