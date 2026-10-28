"use client";

import ValidationReportView from "./ValidationReportView";

/**
 * Validation Audit View
 * Seamlessly routes the Validation Audit tab to the real Validator Engine v2 (Port 8002) report.
 */
export default function ValidationView() {
  return <ValidationReportView />;
}
