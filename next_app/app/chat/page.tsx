"use client";

import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ArchitecturePanel from "@/components/ArchitecturePanel";
import ExplainModal from "@/components/ExplainModal";
import ChatTopBar from "@/components/ChatTopBar";

export default function ChatPage() {
  return (
    <div className="chat-space flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="chat-surface flex min-w-0 flex-1 flex-col">
        <ChatTopBar />
        <div className="flex min-h-0 flex-1 overflow-hidden">
          <ChatWindow />
          <ArchitecturePanel />
        </div>
      </div>
      <ExplainModal />
    </div>
  );
}
