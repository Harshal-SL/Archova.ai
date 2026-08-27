"use client";

import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ArchitecturePanel from "@/components/ArchitecturePanel";
import ExplainModal from "@/components/ExplainModal";

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col bg-[#0A0A0A] font-sans">
      <Navbar /> {/* Now renders null on /chat */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatWindow />
        <ArchitecturePanel />
      </div>
      <ExplainModal />
    </div>
  );
}
