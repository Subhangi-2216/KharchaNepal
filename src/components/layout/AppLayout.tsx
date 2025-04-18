
import { Sidebar } from "./Sidebar";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden bg-background w-full transition-all duration-300">
        <div className="container mx-auto py-6 px-4 md:px-6 max-w-7xl">
          {children}
        </div>
      </main>
    </div>
  );
}
