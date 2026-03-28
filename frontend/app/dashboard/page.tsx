"use client"

import { useState, useEffect } from "react"
import { healthCheck, type HealthCheckResponse } from "../../lib/api"
import { DashboardSidebar } from "@/components/dashboard/dashboard-sidebar"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { StatCards } from "@/components/dashboard/stat-cards"
import { TrafficChartPanel, PacketInspectionPanel, TrafficAnalysisPanel } from "@/components/dashboard/traffic"
import { BlockedSitesCard, ObservedDevicesCard, ThreatDetectionPanel, ThreatResponsePanel, OSProtection } from "@/components/dashboard/threats"
import { SettingsPanel, AdminPanel, ActionLogs } from "@/components/dashboard/admin"
import { AlertNotifications, NotificationArchive } from "@/components/dashboard/alerts"

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

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
    <div className="flex min-h-screen overflow-hidden bg-background">
      <DashboardSidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        mobileOpen={mobileNavOpen}
        onMobileOpenChange={setMobileNavOpen}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onMenuClick={() => setMobileNavOpen(true)}
        />
        <main className="flex-1 space-y-6 overflow-y-auto p-4 sm:p-6">
          {activeTab === "overview" && (
            <>
              <StatCards healthData={healthData} />
              <div className="grid gap-4 xl:grid-cols-3">
                <div className="lg:col-span-2">
                  <TrafficChartPanel />
                </div>
                <div className="space-y-4">
                  <ObservedDevicesCard />
                  <ThreatDetectionPanel />
                </div>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <ThreatResponsePanel />
                <AlertNotifications />
              </div>
              <BlockedSitesCard />
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
              <div className="grid gap-4 lg:grid-cols-2">
                <ThreatResponsePanel />
                <AlertNotifications />
              </div>
              <BlockedSitesCard />
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
