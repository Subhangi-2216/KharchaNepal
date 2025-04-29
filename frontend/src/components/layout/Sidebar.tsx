import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  Home, 
  Receipt, 
  PieChart, 
  Settings, 
  ChevronLeft, 
  ChevronRight, 
  LogOut 
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
          ? "bg-white/20 text-white" 
          : "text-white/70 hover:bg-white/10"
      )}
    >
      <Icon size={20} />
      {!isCollapsed && <span>{label}</span>}
    </Link>
  );
};

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    navigate('/login');
  };

  return (
    <div 
      className={cn(
        "h-screen flex flex-col bg-blue-600 transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo/Header */}
      <div className="p-4 flex items-center justify-between text-white">
        {!collapsed && (
          <h1 className="text-lg font-bold">
            Kharcha Nepal
          </h1>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-full hover:bg-white/10 text-white"
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

        <div className="mt-auto">
          <button 
            onClick={handleLogout}
            className={cn(
              "flex items-center w-full gap-3 px-3 py-2 rounded-md transition-colors",
              "text-white/70 hover:bg-white/10"
            )}
          >
            <LogOut size={20} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4">
        {!collapsed && (
          <div className="text-xs text-white/60">
            KharchaNP v1.0
          </div>
        )}
      </div>
    </div>
  );
}
