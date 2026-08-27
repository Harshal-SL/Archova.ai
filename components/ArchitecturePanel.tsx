"use client";

import { useAppStore } from "@/lib/store";
import ArsrsView from "./ArsrsView";
import HldView from "./HldView";
import LldsView from "./LldsView";
import ChatWindow from "./ChatWindow";

export default function ArchitecturePanel() {
  const { activePipelineStep } = useAppStore();

  switch (activePipelineStep) {
    case 2:
      return <ArsrsView />;
    case 3:
      return <HldView />;
    case 4:
      return <LldsView />;
    default:
      return <ChatWindow />;
  }
}
