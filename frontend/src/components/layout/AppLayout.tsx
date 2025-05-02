
import { useState, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Menu, X } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Handle scroll for header shadow
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Get user initials for avatar
  const getUserInitials = () => {
    // Fallback to "U" if user or user.name is not available
    if (!user || !user.name) return "U";

    try {
      return user.name
        .split(" ")
        .map(part => part[0])
        .join("")
        .toUpperCase()
        .substring(0, 2);
    } catch (error) {
      console.error("Error generating user initials:", error);
      return "U";
    }
  };

  return (
    <div className="flex min-h-screen flex-col md:flex-row bg-muted/30">
      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - hidden on mobile unless menu is open */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out md:sticky md:top-0 md:h-screen md:transform-none md:flex-shrink-0",
        isMobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        <Sidebar />
      </aside>

      {/* Main content */}
      <main className="flex-1 w-full transition-all duration-300">
        {/* Header */}
        <header className={cn(
          "sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6",
          scrolled && "shadow-sm"
        )}>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          <div className="w-full flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-medium hidden md:block">
                {location.pathname === "/" ? "Dashboard" :
                 location.pathname === "/expenses" ? "Expenses" :
                 location.pathname === "/reports" ? "Reports" :
                 location.pathname === "/settings" ? "Settings" : ""}
              </h2>
            </div>

            <div className="flex items-center gap-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full" aria-label="User menu">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/avatar.png" alt="User" />
                      <AvatarFallback>{getUserInitials()}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/settings")}>
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout}>
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="container mx-auto py-6 px-4 md:px-6 max-w-7xl">
          {children}
        </div>
      </main>
    </div>
  );
}
