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
    const [showAllCategories, setShowAllCategories] = useState(false)
    const [stats, setStats] = useState({
        total_emails: 0,
        classified_count: 0,
        unclassified_count: 0,
        average_confidence: 0,
        category_breakdown: {} // Dynamic categories from database
    })
    const [previousStats, setPreviousStats] = useState(null)
    const [pollingStatus, setPollingStatus] = useState(null)

    const CATEGORY_COLORS = {
        hr: "#EC4899",           // Pink
        finance: "#10B981",      // Green
        marketing: "#3B82F6",    // Blue
        it_support: "#8B5CF6",   // Purple
        operations: "#F59E0B",   // Amber
        general: "#6B7280",      // Gray
        sales: "#EF4444",        // Red
        legal: "#14B8A6",        // Teal
        executive: "#F97316",    // Orange
        updates: "#A855F7",      // Purple
        promotion: "#3B82F6",    // Blue
        social: "#10B981",       // Green
        important: "#F97316",    // Orange
        customer_service: "#06B6D4", // Cyan
        spam: "#EF4444"          // Red
    }

    const getCategoryColor = (category) => CATEGORY_COLORS[category] || "#6B7280"


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

            // Calculate category breakdown from classifications - DYNAMIC
            const categoryBreakdown = {}
            let totalConfidence = 0
            let classifiedCount = 0
            let totalEmails = 0

            classRes.data.classifications?.forEach(email => {
                totalEmails++
                // Only count valid categories (exclude pending, null, or empty)
                if (email.category && email.category !== 'pending' && email.category.trim() !== '') {
                    // Dynamically count all categories
                    if (!categoryBreakdown[email.category]) {
                        categoryBreakdown[email.category] = 0
                    }
                    categoryBreakdown[email.category]++
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
        <div className="flex-1 flex flex-col h-screen bg-transparent">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
                                Dashboard
                            </h2>
                            <p className="text-sm text-muted-foreground">Monitor your email classification performance</p>
                        </div>
                        <Button 
                            onClick={() => fetchData(false)} 
                            disabled={refreshing}
                            className="shadow-lg hover:shadow-xl transition-all"
                        >
                            <RefreshCw className={cn("mr-2 h-4 w-4", refreshing && "animate-spin")} />
                            Refresh Data
                        </Button>
                    </div>

                    {/* Statistics Cards with Trending */}
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-blue-100">Total Emails</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.total_emails, previousStats.total_emails) && (
                                    <span className={cn("text-xs font-semibold px-2 py-1 rounded-full", 
                                        calculateTrend(stats.total_emails, previousStats.total_emails).isUp 
                                            ? "bg-green-500/20 text-green-100" 
                                            : "bg-red-500/20 text-red-100")}>
                                        {calculateTrend(stats.total_emails, previousStats.total_emails).isUp ? "↑" : "↓"}{calculateTrend(stats.total_emails, previousStats.total_emails).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{stats.total_emails}</div>
                                )}
                                <p className="text-xs text-blue-100">Processed by AI</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-purple-100">Classified</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.classified_count, previousStats.classified_count) && (
                                    <span className={cn("text-xs font-semibold px-2 py-1 rounded-full",
                                        calculateTrend(stats.classified_count, previousStats.classified_count).isUp
                                            ? "bg-green-500/20 text-green-100"
                                            : "bg-red-500/20 text-red-100")}>
                                        {calculateTrend(stats.classified_count, previousStats.classified_count).isUp ? "↑" : "↓"}{calculateTrend(stats.classified_count, previousStats.classified_count).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{stats.classified_count}</div>
                                )}
                                <p className="text-xs text-purple-100">Successfully categorized</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-green-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-green-100">Avg Confidence</CardTitle>
                                {!loading && previousStats && calculateTrend(stats.average_confidence, previousStats.average_confidence) && (
                                    <span className={cn("text-xs font-semibold px-2 py-1 rounded-full",
                                        calculateTrend(stats.average_confidence, previousStats.average_confidence).isUp
                                            ? "bg-green-500/20 text-green-100"
                                            : "bg-red-500/20 text-red-100")}>
                                        {calculateTrend(stats.average_confidence, previousStats.average_confidence).isUp ? "↑" : "↓"}{calculateTrend(stats.average_confidence, previousStats.average_confidence).percent}%
                                    </span>
                                )}
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-20 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{(stats.average_confidence * 100).toFixed(1)}%</div>
                                )}
                                <p className="text-xs text-green-100">Model certainty</p>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-500 to-orange-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-orange-100">Gmail Status</CardTitle>
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-6 w-24 mb-1 bg-white/20" />
                                ) : (
                                    pollingStatus?.gmail_connected ? (
                                        <div className="flex items-center font-bold text-xl mb-1">
                                            <span className="flex h-3 w-3 rounded-full bg-green-400 mr-2 animate-pulse shadow-lg shadow-green-400/50" />
                                            Connected
                                        </div>
                                    ) : (
                                        <div className="flex items-center text-orange-100 text-xl mb-1">
                                            <span className="flex h-3 w-3 rounded-full bg-white/50 mr-2" />
                                            Disconnected
                                        </div>
                                    )
                                )}
                                <p className="text-xs text-orange-100">Live Polling</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Category Distribution Cards Grid */}
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">Top Categories</h3>
                            {Object.keys(stats.category_breakdown).length > 6 && (
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    onClick={() => setShowAllCategories(!showAllCategories)}
                                >
                                    {showAllCategories ? 'Show Less' : `Show All (${Object.keys(stats.category_breakdown).length})`}
                                </Button>
                            )}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {Object.entries(stats.category_breakdown)
                                .sort(([, a], [, b]) => b - a) // Sort by count descending
                                .slice(0, showAllCategories ? undefined : 6) // Show only top 6 by default
                                .map(([category, count]) => {
                                    const percentage = stats.classified_count > 0
                                        ? ((count / stats.classified_count) * 100).toFixed(1)
                                        : 0
                                    const categoryColor = getCategoryColor(category)

                                    return (
                                        <Card key={category} className="group border-0 hover:shadow-xl transition-all duration-300 bg-white/90 backdrop-blur overflow-hidden relative" style={{ borderLeft: `4px solid ${categoryColor}` }}>
                                            <div className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-10 -translate-y-8 translate-x-8 group-hover:scale-150 transition-transform duration-500" style={{ backgroundColor: categoryColor }}></div>
                                            <CardContent className="pt-6 relative z-10">
                                                <div className="flex items-center gap-2 mb-4">
                                                    <div
                                                        className="w-3 h-3 rounded-full shadow-lg animate-pulse"
                                                        style={{ backgroundColor: categoryColor }}
                                                    />
                                                    <h4 className="font-semibold text-base capitalize group-hover:text-blue-600 transition-colors">{category.replace(/_/g, ' ')}</h4>
                                                </div>

                                                <div className="mb-4">
                                                    <div className="text-3xl font-bold mb-1" style={{ color: categoryColor }}>{count}</div>
                                                    <div className="text-xs text-muted-foreground font-medium">{percentage}% of classified</div>
                                                </div>

                                                {/* Progress Bar */}
                                                <div className="w-full bg-gray-100 rounded-full h-2.5 shadow-inner">
                                                    <div
                                                        className="h-2.5 rounded-full transition-all duration-500 shadow-sm"
                                                        style={{
                                                            width: `${percentage}%`,
                                                            backgroundColor: categoryColor
                                                        }}
                                                    />
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )
                                })}
                        </div>
                    </div>

                    {/* Pie Chart Section - More Compact */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Category Distribution Chart</CardTitle>
                            <CardDescription>Visual breakdown of all classified emails</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading || stats.classified_count === 0 ? (
                                <div className="flex items-center justify-center h-48 text-muted-foreground">
                                    {stats.classified_count === 0 ? "No classified emails yet" : "Loading chart..."}
                                </div>
                            ) : (
                                <div className="h-[400px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={Object.entries(stats.category_breakdown).map(([name, value]) => ({
                                                    name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                                                    value: value
                                                }))}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, percent }) => percent > 0.05 ? `${name}: ${(percent * 100).toFixed(1)}%` : ''}
                                                outerRadius={120}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {Object.keys(stats.category_breakdown).map((category) => (
                                                    <Cell key={category} fill={getCategoryColor(category)} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                formatter={(value, name) => [`${value} emails`, name]}
                                            />
                                            <Legend 
                                                layout="vertical" 
                                                align="right" 
                                                verticalAlign="middle"
                                                wrapperStyle={{ paddingLeft: '20px' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    )
}

export default DashboardPage
