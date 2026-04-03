// User profile modal used for showing account details in the dashboard UI.
import { User, Mail, Shield } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { User as UserData } from "@/lib/api"

interface UserProfileModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user: UserData | null
}

export function UserProfileModal({ open, onOpenChange, user }: UserProfileModalProps) {
  if (!user) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            User Profile
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Avatar Section */}
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
              <User className="h-8 w-8 text-primary" />
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">{user.email}</p>
              <Badge className="mt-1">{user.role}</Badge>
            </div>
          </div>

          {/* Profile Information */}
          <Card className="p-4">
            <div className="grid gap-3">
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="text-sm font-medium text-foreground">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Shield className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Role</p>
                  <p className="text-sm font-medium text-foreground">{user.role}</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}
