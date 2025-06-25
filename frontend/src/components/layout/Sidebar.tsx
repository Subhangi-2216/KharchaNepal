import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  Home,
  Receipt,
  PieChart,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  CreditCard,
  BarChart4
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface SidebarLinkProps {
  to: string;
  icon: React.ElementType;
  label: string;
  isCollapsed: boolean;
}

const SidebarLink = ({ to, icon: Icon, label, isCollapsed }: SidebarLinkProps) => {
  const { pathname } = useLocation();
  const isActive = pathname === to || (to !== "/" && pathname.startsWith(to));

  const linkContent = (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-3 rounded-lg transition-all duration-200",
        isCollapsed ? "justify-center py-3 px-2" : "px-3 py-3",
        isActive
          ? "bg-primary text-primary-foreground font-medium shadow-sm"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
      aria-label={label}
      tabIndex={0}
    >
      <Icon size={isCollapsed ? 20 : 18} className={cn(isActive ? "text-primary-foreground" : "text-muted-foreground/80")} />
      {!isCollapsed && <span>{label}</span>}
    </Link>
  );

  if (isCollapsed) {
    return (
      <TooltipProvider delayDuration={100}>
        <Tooltip>
          <TooltipTrigger asChild>
            {linkContent}
          </TooltipTrigger>
          <TooltipContent side="right" align="start" className="font-medium">
            {label}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return linkContent;
};

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if we're on mobile and auto-collapse sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true);
      }
    };

    // Set initial state
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Clean up
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close sidebar on navigation on mobile
  useEffect(() => {
    if (window.innerWidth < 768) {
      setCollapsed(true);
    }
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    navigate('/login');
  };

  return (
    <div
      className={cn(
        "h-screen flex flex-col bg-card border-r border-border transition-all duration-300 shadow-sm",
        collapsed ? "w-[80px]" : "w-[240px]"
      )}
    >
      {/* Logo/Header */}
      <div className={cn(
        "border-b border-border",
        collapsed ? "p-2" : "p-4"
      )}>
        {!collapsed ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              <h1 className="text-lg font-semibold tracking-tight">
                KharchaNP
              </h1>
            </div>
            <button
              onClick={() => setCollapsed(true)}
              className="p-1.5 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft size={16} />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <CreditCard className="h-6 w-6 text-primary" />
            <button
              onClick={() => setCollapsed(false)}
              className="p-1.5 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Expand sidebar"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex-1 px-2 py-6 flex flex-col gap-1.5">
        <div className={cn("mb-1 px-3", !collapsed && "mb-2")}>
          {!collapsed && (
            <p className="text-xs font-medium text-muted-foreground mb-2">DASHBOARD</p>
          )}
          <SidebarLink to="/" icon={Home} label="Overview" isCollapsed={collapsed} />
        </div>

        <div className={cn("mb-1 px-3", !collapsed && "mb-2")}>
          {!collapsed && (
            <p className="text-xs font-medium text-muted-foreground mb-2">MANAGE</p>
          )}
          <SidebarLink to="/expenses" icon={Receipt} label="Expenses" isCollapsed={collapsed} />
          <SidebarLink to="/reports" icon={BarChart4} label="Reports" isCollapsed={collapsed} />
        </div>

        <div className={cn("mb-1 px-3", !collapsed && "mb-2")}>
          {!collapsed && (
            <p className="text-xs font-medium text-muted-foreground mb-2">ACCOUNT</p>
          )}
          <SidebarLink to="/settings" icon={Settings} label="Settings" isCollapsed={collapsed} />
        </div>

        <div className="mt-auto px-3">
          {collapsed ? (
            <TooltipProvider delayDuration={100}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full justify-center p-3 rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                    aria-label="Logout"
                  >
                    <LogOut size={18} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" align="start" className="font-medium">
                  Logout
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <button
              onClick={handleLogout}
              className="flex items-center w-full gap-3 px-3 py-3 rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
            >
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className={cn(
        "border-t border-border",
        collapsed ? "p-3" : "p-4"
      )}>
        {!collapsed ? (
          <div className="text-xs text-muted-foreground flex items-center justify-between">
            <span>KharchaNP v1.0</span>
            <span>© 2025</span>
          </div>
        ) : (
          <div className="flex justify-center">
            <CreditCard className="h-4 w-4 text-muted-foreground/50" />
          </div>
        )}
      </div>
    </div>
  );
}
