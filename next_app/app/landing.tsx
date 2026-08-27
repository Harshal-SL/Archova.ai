"use client";

import Link from "next/link";
import { ArrowRight, Box, Component, Share2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import { motion } from "framer-motion";

const features = [
  {
    icon: Box,
    title: "Instant HLD",
    desc: "Generate High-Level Designs for complex architectures instantly by just typing a prompt.",
  },
  {
    icon: Component,
    title: "Drill-down LLD",
    desc: "Click into any component to explore detailed Low-Level Designs with pseudo-code and patterns.",
  },
  {
    icon: Share2,
    title: "Export & Share",
    desc: "Share your architecture diagrams with your team or export them for your technical specifications.",
  },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-black overflow-hidden font-sans">
      {/* Animated Subtle Grid Background */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]">
        <div
          className="absolute inset-0 z-0"
          style={{
            backgroundImage: "linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
      </div>

      {/* Subtle Noise Texture overlay */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.02]" 
        style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }} 
      />

      <Navbar />

      <main className="relative z-10 flex flex-col items-center justify-center pt-32 px-6">
        {/* Hero Section */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex flex-col items-center text-center max-w-4xl pt-16 pb-24"
        >
          <div className="mb-6 inline-flex items-center rounded-full border border-[#555555] bg-[#111111] px-4 py-1.5 text-xs font-semibold text-[#AAAAAA]">
            v2.0 Now Available
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
            Design Systems <br className="hidden md:block"/> Instantly with AI
          </h1>
          <p className="text-lg md:text-xl text-[#AAAAAA] max-w-2xl mb-10 leading-relaxed font-mono">
            Enter a prompt. Get a complete HLD + LLD system design in seconds.
          </p>
          
          <Link
            href="/chat"
            className="group relative flex items-center gap-2 rounded-full border border-black bg-white px-8 py-4 text-base font-bold text-black transition-transform hover:scale-105 active:scale-95"
          >
            Start Designing
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>
        </motion.section>

        {/* Feature Highlights Section */}
        <section className="w-full max-w-5xl grid gap-6 md:grid-cols-3 pb-32">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="flex flex-col items-start p-8 rounded-2xl border border-[#333333] bg-[#111111] hover:bg-[#1A1A1A] transition-colors"
            >
              <div className="mb-6 p-3 rounded-full border border-[#555555] bg-black">
                <feature.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-[#AAAAAA] leading-relaxed">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </section>
      </main>
    </div>
  );
}
