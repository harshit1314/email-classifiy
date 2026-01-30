import React from 'react'
import { Sidebar } from './Sidebar'
import { Outlet } from 'react-router-dom'

const DashboardLayout = () => {
    return (
        <div className="flex h-screen overflow-hidden bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
                <div className="min-h-full">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}

export { DashboardLayout }
