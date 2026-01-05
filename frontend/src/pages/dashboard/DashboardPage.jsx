import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/use-toast"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const DashboardPage = () => {
    const { API_URL, token } = useAuth()
    const { toast } = useToast()
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [stats, setStats] = useState({
        total_emails: 0,
        classified_count: 0,
        unclassified_count: 0,
        average_confidence: 0,
        category_breakdown: {
            spam: 0,
            important: 0,
            promotion: 0,
            social: 0,
            updates: 0
        }
    })
    const [previousStats, setPreviousStats] = useState(null)
    const [pollingStatus, setPollingStatus] = useState(null)

    const CATEGORY_COLORS = {
        spam: "#EF4444",
        important: "#F97316",
        promotion: "#3B82F6",
        social: "#10B981",
        updates: "#A855F7"
    }

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
            spam: "bg-red-50",
            important: "bg-orange-50",
            promotion: "bg-blue-50",
            social: "bg-green-50",
            updates: "bg-purple-50"
        }
        return colors[category] || "bg-gray-50"
    }

    const getCategoryBorderColor = (category) => {
        const colors = {
            spam: "border-red-200",
            important: "border-orange-200",
            promotion: "border-blue-200",
            social: "border-green-200",
            updates: "border-purple-200"
        }
        return colors[category] || "border-gray-200"
    }

    const calculateTrend = (currentValue, previousValue) => {
        if (!previousValue || previousValue === 0) return null
        const change = ((currentValue - previousValue) / previousValue) * 100
        return {
            percent: Math.abs(change).toFixed(1),
            isUp: change >= 0
        }
    }

    const fetchData = async (isAutoRefresh = false) => {
        if (!isAutoRefresh) setLoading(true)
        setRefreshing(true)
        try {
            const [statsRes, classRes, statusRes] = await Promise.all([
                axios.get(`${API_URL}/api/dashboard/statistics`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/dashboard/classifications?limit=1000`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/email/status`)
            ])

            // Calculate category breakdown from classifications
            const categoryBreakdown = {
                spam: 0,
                important: 0,
                promotion: 0,
                social: 0,
                updates: 0
            }
            let totalConfidence = 0
            let classifiedCount = 0
            let totalEmails = 0
            
            classRes.data.classifications?.forEach(email => {
                totalEmails++
                if (email.category) {
                    if (categoryBreakdown.hasOwnProperty(email.category)) {
                        categoryBreakdown[email.category]++
                    }
                    totalConfidence += email.confidence || 0
                    classifiedCount++
                }
            })

            // Use ONLY calculated values, not backend stats
            const enrichedStats = {
                total_emails: totalEmails,
                classified_count: classifiedCount,
                unclassified_count: totalEmails - classifiedCount,
                average_confidence: classifiedCount > 0 ? totalConfidence / classifiedCount : 0,
                category_breakdown: categoryBreakdown
            }

            // Store current stats as previous stats for next fetch
            setPreviousStats(stats)
            setStats(enrichedStats)
            setPollingStatus(statusRes.data)
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err)
            toast({
                variant: "destructive",
                title: "Failed to update dashboard",
                description: "Could not fetch latest stats from backend.",
            })
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(() => fetchData(true), 30000) // Refresh every 30s silently
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="flex-1 flex flex-col h-screen bg-background">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                        <Button onClick={() => fetchData(false)} disabled={refreshing}>
                            <RefreshCw className={cn("mr-2 h-4 w-4", refreshing && "animate-spin")} />
                            Refresh Data
                        </Button>
                    </div>

                    {/* Statistics Cards with Trending */}
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.total_emails, previousStats.total_emails) && (
                                    <span className={cn("text-xs font-semibold", calculateTrend(stats.total_emails, previousStats.total_emails).isUp ? "text-green-600" : "text-red-600")}>
                                        {calculateTrend(stats.total_emails, previousStats.total_emails).isUp ? "+" : ""}{calculateTrend(stats.total_emails, previousStats.total_emails).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent>
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1" />
                                ) : (
                                    <div className="text-2xl font-bold">{stats.total_emails}</div>
                                )}
                                <p className="text-xs text-muted-foreground">Processed by BERT</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Classified</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.classified_count, previousStats.classified_count) && (
                                    <span className={cn("text-xs font-semibold", calculateTrend(stats.classified_count, previousStats.classified_count).isUp ? "text-green-600" : "text-red-600")}>
                                        {calculateTrend(stats.classified_count, previousStats.classified_count).isUp ? "+" : ""}{calculateTrend(stats.classified_count, previousStats.classified_count).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent>
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1" />
                                ) : (
                                    <div className="text-2xl font-bold">{stats.classified_count}</div>
                                )}
                                <p className="text-xs text-muted-foreground">Successfully categorized</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.average_confidence, previousStats.average_confidence) && (
                                    <span className={cn("text-xs font-semibold", calculateTrend(stats.average_confidence, previousStats.average_confidence).isUp ? "text-green-600" : "text-red-600")}>
                                        {calculateTrend(stats.average_confidence, previousStats.average_confidence).isUp ? "+" : ""}{calculateTrend(stats.average_confidence, previousStats.average_confidence).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent>
                                {loading ? (
                                    <Skeleton className="h-8 w-20 mb-1" />
                                ) : (
                                    <div className="text-2xl font-bold">{(stats.average_confidence * 100).toFixed(1)}%</div>
                                )}
                                <p className="text-xs text-muted-foreground">Model certainty</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Gmail Status</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {loading ? (
                                    <Skeleton className="h-6 w-24 mb-1" />
                                ) : (
                                    pollingStatus?.gmail_connected ? (
                                        <div className="flex items-center text-green-600 font-bold">
                                            <span className="flex h-3 w-3 rounded-full bg-green-600 mr-2" />
                                            Connected
                                        </div>
                                    ) : (
                                        <div className="flex items-center text-muted-foreground">
                                            <span className="flex h-3 w-3 rounded-full bg-gray-300 mr-2" />
                                            Disconnected
                                        </div>
                                    )
                                )}
                                <p className="text-xs text-muted-foreground mt-1">Live Polling</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Category Distribution Cards Grid */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Category Distribution</h3>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
                            {['spam', 'important', 'promotion', 'social', 'updates'].map((category) => {
                                const count = stats.category_breakdown[category] || 0
                                const percentage = stats.classified_count > 0 
                                    ? ((count / stats.classified_count) * 100).toFixed(1)
                                    : 0
                                
                                return (
                                    <Card key={category} className={cn("border-l-4", getCategoryBorderColor(category), getCategoryBgColor(category))}>
                                        <CardContent className="pt-6">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-2">
                                                    <div 
                                                        className="w-3 h-3 rounded-full" 
                                                        style={{backgroundColor: CATEGORY_COLORS[category]}}
                                                    />
                                                    <h4 className="font-semibold text-sm capitalize">{category}</h4>
                                                </div>
                                            </div>
                                            
                                            <div className="mb-3">
                                                <div className="text-2xl font-bold mb-1">{count}</div>
                                                <div className="text-xs text-muted-foreground">{percentage}% of classified</div>
                                            </div>

                                            {/* Progress Bar */}
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div 
                                                    className="h-2 rounded-full transition-all duration-300" 
                                                    style={{
                                                        width: `${percentage}%`,
                                                        backgroundColor: CATEGORY_COLORS[category]
                                                    }}
                                                />
                                            </div>
                                        </CardContent>
                                    </Card>
                                )
                            })}
                        </div>
                    </div>

                    {/* Pie Chart Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Email Category Distribution</CardTitle>
                            <CardDescription>Visual breakdown of classified emails by category</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading || stats.classified_count === 0 ? (
                                <div className="flex items-center justify-center h-64 text-muted-foreground">
                                    {stats.classified_count === 0 ? "No classified emails yet" : "Loading chart..."}
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={Object.entries(stats.category_breakdown).map(([name, value]) => ({
                                                name: name.charAt(0).toUpperCase() + name.slice(1),
                                                value: value
                                            }))}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                                            outerRadius={100}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {Object.keys(stats.category_breakdown).map((category) => (
                                                <Cell key={category} fill={CATEGORY_COLORS[category]} />
                                            ))}
                                        </Pie>
                                        <Tooltip 
                                            formatter={(value) => [`${value} emails`, 'Count']}
                                        />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            )}
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    )
}

export default DashboardPage
