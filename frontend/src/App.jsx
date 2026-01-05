import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import EmailsPage from '@/pages/dashboard/EmailsPage'
import LiveIngestionsPage from '@/pages/dashboard/LiveIngestionsPage'
import EmailConnectPage from '@/pages/email/EmailConnectPage'
import EmailClassifyPage from '@/pages/email/EmailClassifyPage'
import CalendarPage from '@/pages/dashboard/CalendarPage'
import SettingsPage from '@/pages/dashboard/SettingsPage'
import FiltersPage from '@/pages/settings/FiltersPage'
import { Toaster } from "@/components/ui/toaster"
import ErrorBoundary from "@/components/ErrorBoundary"

// Protected Route Component
const ProtectedRoute = () => {
    const { isAuthenticated, loading } = useAuth()

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Loading...</div>
    }

    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

function App() {
    return (
        <Router>
            <ErrorBoundary>
                <AuthProvider>
                    <Routes>
                        {/* Public Routes */}
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />

                        {/* Protected Routes */}
                        <Route element={<ProtectedRoute />}>
                            <Route element={<DashboardLayout />}>
                                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                                <Route path="/dashboard" element={<DashboardPage />} />
                                <Route path="/emails" element={<EmailsPage />} />
                                <Route path="/live-ingestions" element={<LiveIngestionsPage />} />
                                <Route path="/connect" element={<EmailConnectPage />} />
                                <Route path="/classify" element={<EmailClassifyPage />} />
                                <Route path="/calendar" element={<CalendarPage />} />
                                <Route path="/settings" element={<SettingsPage />} />
                                <Route path="/settings/filters" element={<FiltersPage />} />
                            </Route>
                        </Route>

                        {/* Catch all */}
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                    <Toaster />
                </AuthProvider>
            </ErrorBoundary>
        </Router>
    )
}

export default App
