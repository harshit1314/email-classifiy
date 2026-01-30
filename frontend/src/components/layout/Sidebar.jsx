import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    Mail,
    Search,
    Settings,
    LogOut,
    Calendar,
    ShieldAlert,
    Inbox,
    Sparkles,
    ChevronRight,
    User
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'

const Sidebar = () => {
    const { logout, user } = useAuth()
    const [hoveredItem, setHoveredItem] = useState(null)

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard', color: 'from-blue-500 to-cyan-500' },
        { icon: Mail, label: 'Emails', to: '/emails', color: 'from-purple-500 to-pink-500' },
        { icon: Inbox, label: 'Live Ingestions', to: '/live-ingestions', color: 'from-green-500 to-emerald-500' },
        { icon: Calendar, label: 'Calendar', to: '/calendar', color: 'from-orange-500 to-red-500' },
        { icon: Settings, label: 'Settings', to: '/settings', color: 'from-gray-500 to-slate-500' },
        { icon: ShieldAlert, label: 'Connect', to: '/connect', color: 'from-indigo-500 to-violet-500' },
    ]

    return (
        <div className="flex flex-col h-full w-64 bg-white/80 backdrop-blur-xl border-r border-gray-200/50 shadow-xl">
            {/* Header */}
            <div className="p-6 border-b border-gray-100">
                <div className="flex items-center gap-3 mb-1">
                    <div className="rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 p-2 shadow-lg">
                        <Sparkles className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                            EmailIQ
                        </h1>
                    </div>
                </div>
                <p className="text-xs text-muted-foreground ml-11">AI Email Classifier</p>
            </div>

            {/* User Profile Section */}
            {user && (
                <div className="mx-4 mt-4 mb-2">
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold shadow-md">
                            {user.email?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 truncate">
                                {user.full_name || 'User'}
                            </p>
                            <p className="text-xs text-gray-600 truncate">{user.email}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {navItems.map((item, index) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        onMouseEnter={() => setHoveredItem(index)}
                        onMouseLeave={() => setHoveredItem(null)}
                        className={({ isActive }) =>
                            cn(
                                "group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-gradient-to-r " + item.color + " text-white shadow-lg shadow-blue-500/20"
                                    : "text-gray-700 hover:bg-gray-100/80"
                            )
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <item.icon className={cn(
                                    "h-5 w-5 transition-transform duration-200",
                                    hoveredItem === index && !isActive && "scale-110"
                                )} />
                                <span className="flex-1">{item.label}</span>
                                {isActive && (
                                    <ChevronRight className="h-4 w-4 animate-in slide-in-from-left-1" />
                                )}
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-gray-100">
                <Button
                    variant="ghost"
                    className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 transition-all duration-200 group"
                    onClick={logout}
                >
                    <LogOut className="mr-3 h-4 w-4 group-hover:scale-110 transition-transform" />
                    <span className="font-medium">Logout</span>
                </Button>
            </div>
        </div>
    )
}

export { Sidebar }
