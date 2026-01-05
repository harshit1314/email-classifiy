import React from 'react'
import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    Mail,
    Search,
    Settings,
    LogOut,
    Calendar,
    ShieldAlert,
    Inbox
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'

const Sidebar = () => {
    const { logout } = useAuth()

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
        { icon: Mail, label: 'Emails', to: '/emails' },
        { icon: Inbox, label: 'Live Ingestions', to: '/live-ingestions' },
        { icon: Calendar, label: 'Calendar', to: '/calendar' },
        { icon: Settings, label: 'Settings', to: '/settings' },
        { icon: ShieldAlert, label: 'Connect', to: '/connect' },
    ]

    return (
        <div className="flex flex-col h-full w-64 bg-card border-r">
            <div className="p-6">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                    EmailIQ
                </h1>
                <p className="text-sm text-muted-foreground mt-1">AI Email Classifier</p>
            </div>

            <nav className="flex-1 px-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            )
                        }
                    >
                        <item.icon className="h-5 w-5" />
                        {item.label}
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t">
                <Button
                    variant="ghost"
                    className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50"
                    onClick={logout}
                >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                </Button>
            </div>
        </div>
    )
}

export { Sidebar }
