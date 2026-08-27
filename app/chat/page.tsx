"use client";

import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import PipelineStepper from "@/components/PipelineStepper";
import ChatWindow from "@/components/ChatWindow";
import ArsrsView from "@/components/ArsrsView";
import HldView from "@/components/HldView";
import LldsView from "@/components/LldsView";
import ExplainModal from "@/components/ExplainModal";
import { useAppStore } from "@/lib/store";

export default function ChatPage() {
  const { activePipelineStep } = useAppStore();

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-white dark:bg-black">
      <Navbar />
      <div className="flex flex-1 overflow-hidden pt-14 min-h-0">
        <Sidebar />

        {/* Main Step-by-Step / Slider Pipeline Container */}
        <div className="flex flex-1 flex-col overflow-hidden bg-white dark:bg-black min-h-0">
          <PipelineStepper />

          <div className="relative flex flex-1 flex-col overflow-hidden min-h-0">
            {activePipelineStep === 1 && <ChatWindow />}
            {activePipelineStep === 2 && <ArsrsView />}
            {activePipelineStep === 3 && <HldView />}
            {activePipelineStep === 4 && <LldsView />}
          </div>
        </div>
      </div>
      <ExplainModal />
    </div>
  );
}
