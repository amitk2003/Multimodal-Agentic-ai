"use client";
import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Providers } from "@/components/layout/Providers";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <Providers>
      <div className="flex h-screen overflow-hidden">
        <Sidebar
          mobileOpen={mobileSidebarOpen}
          onMobileClose={() => setMobileSidebarOpen(false)}
        />
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <Header onMenuToggle={() => setMobileSidebarOpen((v) => !v)} />
          <main className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6">
            {children}
          </main>
        </div>
      </div>
    </Providers>
  );
}
