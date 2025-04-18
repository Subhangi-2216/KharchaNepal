
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  Home, 
  Receipt, 
  PieChart, 
  Settings, 
  ChevronLeft, 
  ChevronRight 
} from "lucide-react";

interface SidebarLinkProps {
  to: string;
  icon: React.ElementType;
  label: string;
  isCollapsed: boolean;
}

const SidebarLink = ({ to, icon: Icon, label, isCollapsed }: SidebarLinkProps) => {
  const { pathname } = useLocation();
  const isActive = pathname === to;

  return (
    <Link 
      to={to} 
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
        isActive 
          ? "text-sidebar-primary-foreground bg-sidebar-primary" 
          : "text-sidebar-foreground hover:text-sidebar-primary-foreground hover:bg-sidebar-accent/50"
      )}
    >
      <Icon size={20} />
      {!isCollapsed && <span>{label}</span>}
    </Link>
  );
};

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div 
      className={cn(
        "h-screen flex flex-col bg-sidebar-default border-r border-sidebar-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo/Header */}
      <div className="p-4 flex items-center justify-between">
        {!collapsed && (
          <h1 className="text-lg font-bold text-sidebar-primary">
            Kharcha Nepal
          </h1>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-full hover:bg-sidebar-accent/50"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-3 py-4 flex flex-col gap-1">
        <SidebarLink to="/" icon={Home} label="Home" isCollapsed={collapsed} />
        <SidebarLink to="/expenses" icon={Receipt} label="Expenses" isCollapsed={collapsed} />
        <SidebarLink to="/reports" icon={PieChart} label="Reports" isCollapsed={collapsed} />
        <SidebarLink to="/settings" icon={Settings} label="Settings" isCollapsed={collapsed} />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        {!collapsed && (
          <div className="text-xs text-sidebar-foreground opacity-60">
            KharchaNP v1.0
          </div>
        )}
      </div>
    </div>
  );
}
