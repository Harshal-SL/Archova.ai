"use client";

import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ArchitecturePanel from "@/components/ArchitecturePanel";
import ExplainModal from "@/components/ExplainModal";

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col bg-white dark:bg-gray-950">
      <Navbar />
      <div className="flex flex-1 overflow-hidden pt-14">
        <Sidebar />
        <ChatWindow />
        <ArchitecturePanel />
      </div>
      <ExplainModal />
    </div>
  );
}
