"use client"

import { useState } from "react"
import { User, Mail, Phone, MapPin, Shield, Calendar, Edit2, X } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"

interface UserProfileModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onNameChange?: (name: string) => void
}

export function UserProfileModal({ open, onOpenChange, onNameChange }: UserProfileModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [userInfo, setUserInfo] = useState({
    name: "Admin User",
    email: "admin@netguard.io",
    phone: "+1 (555) 123-4567",
    department: "Security Operations",
    location: "New York, USA",
    role: "System Administrator",
    joinDate: "January 15, 2024",
  })

  const [editForm, setEditForm] = useState(userInfo)

  const handleSave = () => {
    setUserInfo(editForm)
    setIsEditing(false)
    if (onNameChange && editForm.name !== userInfo.name) {
      onNameChange(editForm.name)
    }
  }

  const handleCancel = () => {
    setEditForm(userInfo)
    setIsEditing(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            User Profile
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Avatar Section */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">{userInfo.name}</p>
                <Badge className="mt-1">{userInfo.role}</Badge>
              </div>
            </div>
            {!isEditing && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
                className="gap-2"
              >
                <Edit2 className="h-4 w-4" />
                Edit
              </Button>
            )}
          </div>

          {/* Profile Information */}
          <div className="grid gap-4">
            {isEditing ? (
              <>
                {/* Edit Form */}
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-foreground">Full Name</label>
                    <Input
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground">Email</label>
                    <Input
                      value={editForm.email}
                      onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                      type="email"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground">Phone</label>
                    <Input
                      value={editForm.phone}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground">Department</label>
                    <Input
                      value={editForm.department}
                      onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground">Location</label>
                    <Input
                      value={editForm.location}
                      onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 justify-end pt-4">
                  <Button variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave} className="gap-2">
                    Save Changes
                  </Button>
                </div>
              </>
            ) : (
              <>
                {/* View Mode */}
                <Card className="p-4">
                  <div className="grid gap-3">
                    <div className="flex items-center gap-3">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Email</p>
                        <p className="text-sm font-medium text-foreground">{userInfo.email}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Phone</p>
                        <p className="text-sm font-medium text-foreground">{userInfo.phone}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Shield className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Department</p>
                        <p className="text-sm font-medium text-foreground">{userInfo.department}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Location</p>
                        <p className="text-sm font-medium text-foreground">{userInfo.location}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Member Since</p>
                        <p className="text-sm font-medium text-foreground">{userInfo.joinDate}</p>
                      </div>
                    </div>
                  </div>
                </Card>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
