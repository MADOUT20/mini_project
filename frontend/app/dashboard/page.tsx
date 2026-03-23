"use client"

import { useState, useEffect } from "react"
import { healthCheck, type HealthCheckResponse } from "../../lib/api"
import { DashboardSidebar } from "@/components/dashboard/dashboard-sidebar"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { StatCards } from "@/components/dashboard/stat-cards"
import { TrafficChartPanel, PacketInspectionPanel, TrafficAnalysisPanel } from "@/components/dashboard/traffic"
import { ThreatDetectionPanel, ThreatResponsePanel, OSProtection } from "@/components/dashboard/threats"
import { SettingsPanel, AdminPanel, ActionLogs } from "@/components/dashboard/admin"
import { AlertNotifications, NotificationArchive } from "@/components/dashboard/alerts"

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)

  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        const data = await healthCheck()
        setHealthData(data)
      } catch (error) {
        console.error("Failed to fetch health status:", error)
      }
    }

    fetchHealthData()
  }, [])

  return (
    <div className="flex h-screen overflow-hidden">
      <DashboardSidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === "overview" && (
            <>
              <StatCards healthData={healthData} />
              <div className="grid gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <TrafficChartPanel />
                </div>
                <ThreatDetectionPanel />
              </div>
              <ThreatResponsePanel />
            </>
          )}
          {activeTab === "packets" && (
            <>
              <TrafficChartPanel />
              <PacketInspectionPanel />
            </>
          )}
          {activeTab === "inspection" && (
            <PacketInspectionPanel />
          )}
          {activeTab === "threats" && (
            <>
              <div className="grid gap-4 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <PacketInspectionPanel />
                </div>
                <ThreatDetectionPanel />
              </div>
              <ThreatResponsePanel />
              <OSProtection />
            </>
          )}
          {activeTab === "traffic" && (
            <>
              <TrafficChartPanel />
              <TrafficAnalysisPanel />
            </>
          )}
          {activeTab === "actions" && (
            <ActionLogs />
          )}
          {activeTab === "archive" && (
            <NotificationArchive />
          )}
          {activeTab === "settings" && (
            <>
              <SettingsPanel />
              <AdminPanel />
            </>
          )}
        </main>
      </div>
    </div>
  )
}
