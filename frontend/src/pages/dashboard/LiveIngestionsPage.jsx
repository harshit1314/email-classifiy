import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, Mail } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/use-toast"

const LiveIngestionsPage = () => {
    const { API_URL, token } = useAuth()
    const { toast } = useToast()
    const [loading, setLoading] = useState(true)
    const [recentEmails, setRecentEmails] = useState([])
    const [pollingStatus, setPollingStatus] = useState(null)

    const getCategoryColor = (category) => {
        const colors = {
            spam: "bg-red-100 text-red-800",
            important: "bg-orange-100 text-orange-800",
            promotion: "bg-blue-100 text-blue-800",
            social: "bg-green-100 text-green-800",
            updates: "bg-purple-100 text-purple-800"
        }
        return colors[category] || "bg-gray-100 text-gray-800"
    }

    const getCategoryBgColor = (category) => {
        const colors = {
            spam: "bg-red-50 border-red-200",
            important: "bg-orange-50 border-orange-200",
            promotion: "bg-blue-50 border-blue-200",
            social: "bg-green-50 border-green-200",
            updates: "bg-purple-50 border-purple-200"
        }
        return colors[category] || "bg-gray-50 border-gray-200"
    }

    const fetchData = async () => {
        setLoading(true)
        try {
            const [classRes, statusRes] = await Promise.all([
                axios.get(`${API_URL}/api/dashboard/classifications?limit=100`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/email/status`)
            ])

            setRecentEmails((classRes.data.classifications || []).slice(0, 100))
            setPollingStatus(statusRes.data)
        } catch (err) {
            console.error('Failed to fetch ingestion data:', err)
            toast({
                variant: "destructive",
                title: "Failed to update ingestions",
                description: "Could not fetch latest emails from backend.",
            })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 10000) // Refresh every 10s
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="flex-1 flex flex-col h-screen bg-background">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                                <Mail className="h-8 w-8" />
                                Live Email Ingestion
                            </h2>
                            <p className="text-sm text-muted-foreground mt-2">Real-time email stream from Gmail</p>
                        </div>
                        <Button onClick={fetchData} disabled={loading}>
                            <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>

                    {/* Status Card */}
                    <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="font-semibold text-lg">Gmail Connection</h3>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {pollingStatus?.gmail_connected ? (
                                            <span className="text-green-600 font-semibold flex items-center gap-2">
                                                <span className="flex h-3 w-3 rounded-full bg-green-600" />
                                                Connected - Live Polling Active
                                            </span>
                                        ) : (
                                            <span className="text-red-600 font-semibold flex items-center gap-2">
                                                <span className="flex h-3 w-3 rounded-full bg-red-600" />
                                                Disconnected
                                            </span>
                                        )}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <div className="text-2xl font-bold">{recentEmails.length}</div>
                                    <p className="text-xs text-muted-foreground">Recent Ingestions</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Email Grid */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Recent Ingestions (Last 100)</h3>
                        {loading && recentEmails.length === 0 ? (
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {Array(6).fill(0).map((_, i) => (
                                    <div key={i} className="p-4 bg-card rounded border">
                                        <Skeleton className="h-4 w-3/4 mb-3" />
                                        <Skeleton className="h-3 w-1/2 mb-4" />
                                        <Skeleton className="h-6 w-24" />
                                    </div>
                                ))}
                            </div>
                        ) : recentEmails.length === 0 ? (
                            <Card className="text-center py-12">
                                <CardContent>
                                    <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                    <p className="text-muted-foreground">No emails ingested yet</p>
                                    <p className="text-xs text-muted-foreground mt-2">Emails will appear here as they arrive from Gmail</p>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {recentEmails.map((email, idx) => (
                                    <Card 
                                        key={email.id || idx} 
                                        className={cn(
                                            "border-l-4 hover:shadow-md transition-all cursor-pointer",
                                            getCategoryBgColor(email.category)
                                        )}
                                    >
                                        <CardContent className="pt-6">
                                            <div className="space-y-3">
                                                {/* Subject */}
                                                <div>
                                                    <h4 className="font-semibold text-sm line-clamp-2 text-foreground">
                                                        {email.email_subject || '(No Subject)'}
                                                    </h4>
                                                </div>

                                                {/* Sender */}
                                                <div>
                                                    <p className="text-xs text-muted-foreground line-clamp-1">
                                                        <span className="font-medium">From:</span> {email.email_sender || 'Unknown'}
                                                    </p>
                                                </div>

                                                {/* Category & Confidence */}
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    {email.category && (
                                                        <span className={cn("text-xs px-2.5 py-1 rounded font-bold", getCategoryColor(email.category))}>
                                                            {email.category.charAt(0).toUpperCase() + email.category.slice(1)}
                                                        </span>
                                                    )}
                                                    {email.confidence && (
                                                        <span className="text-xs px-2.5 py-1 rounded bg-blue-100 text-blue-800 font-semibold">
                                                            {(email.confidence * 100).toFixed(0)}% confident
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Timestamp */}
                                                <div className="pt-2 border-t">
                                                    <p className="text-xs text-muted-foreground">
                                                        {email.timestamp ? new Date(email.timestamp).toLocaleString() : 'No timestamp'}
                                                    </p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default LiveIngestionsPage
