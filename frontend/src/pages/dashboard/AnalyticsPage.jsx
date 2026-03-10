import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, TrendingDown, Minus, RefreshCw, Calendar, Activity, Download } from 'lucide-react'
import HelpTooltip from '@/components/shared/HelpTooltip'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AnalyticsPage = () => {
    const { token } = useAuth()
    const { toast } = useToast()

    const [loading, setLoading] = useState(true)
    const [timeSeries, setTimeSeries] = useState([])
    const [categoryTimeSeries, setCategoryTimeSeries] = useState({})
    const [heatmap, setHeatmap] = useState(null)
    const [trends, setTrends] = useState(null)

    const fetchAnalytics = async () => {
        setLoading(true)
        try {
            const _cb = new Date().getTime()
            const [timeSeriesRes, categorySeriesRes, heatmapRes, trendsRes] = await Promise.all([
                axios.get(`${API_URL}/api/analytics/timeseries?days=30&_t=${_cb}`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/analytics/category-timeseries?days=30&_t=${_cb}`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/analytics/heatmap?days=30&_t=${_cb}`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/analytics/trends?_t=${_cb}`, { headers: { Authorization: `Bearer ${token}` } })
            ])

            setTimeSeries(timeSeriesRes.data.data || [])
            setCategoryTimeSeries(categorySeriesRes.data.data || {})
            setHeatmap(heatmapRes.data)
            setTrends(trendsRes.data)
        } catch (error) {
            console.error('Error fetching analytics:', error)
            toast({
                title: "Error",
                description: "Failed to load analytics data",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    const downloadReport = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/export/report/pdf`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `analytics_report_${new Date().toISOString().split('T')[0]}.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (error) {
            console.error('Error downloading report:', error)
            toast({
                title: "Download Failed",
                description: "Failed to generate PDF report",
                variant: "destructive"
            })
        }
    }

    useEffect(() => {
        fetchAnalytics()
    }, [])

    const getTrendIcon = (trend) => {
        if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-600" />
        if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-600" />
        return <Minus className="w-4 h-4 text-gray-600" />
    }

    const getTrendColor = (trend) => {
        if (trend === 'up') return 'text-green-600 bg-green-50'
        if (trend === 'down') return 'text-red-600 bg-red-50'
        return 'text-gray-600 bg-gray-50'
    }

    const renderHeatmap = () => {
        if (!heatmap || !heatmap.heatmap) return null

        const maxValue = Math.max(...heatmap.heatmap.flat())

        return (
            <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                    <thead>
                        <tr>
                            <th className="border p-2 bg-gray-50 font-semibold sticky left-0 z-10">Day/Hour</th>
                            {heatmap.hours.map(hour => (
                                <th key={hour} className="border p-1 bg-gray-50">
                                    {hour.toString().padStart(2, '0')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {heatmap.weekdays.map((day, dayIdx) => (
                            <tr key={day}>
                                <td className="border p-2 bg-gray-50 font-semibold sticky left-0">{day}</td>
                                {heatmap.heatmap[dayIdx].map((value, hourIdx) => {
                                    const intensity = maxValue > 0 ? (value / maxValue) : 0
                                    const bgColor = value > 0
                                        ? `rgba(59, 130, 246, ${0.2 + intensity * 0.8})`
                                        : 'transparent'
                                    return (
                                        <td
                                            key={hourIdx}
                                            className="border p-1 text-center"
                                            style={{ backgroundColor: bgColor }}
                                            title={`${day} ${hourIdx}:00 - ${value} emails`}
                                        >
                                            {value || ''}
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div className="mt-3 text-xs text-gray-600">
                    <p>💡 Darker colors indicate higher email volume. Hover over cells to see exact counts.</p>
                </div>
            </div>
        )
    }

    if (loading) {
        return (
            <div className="container mx-auto p-6 space-y-6">
                <Skeleton className="h-12 w-64" />
                <div className="grid gap-6 md:grid-cols-3">
                    <Skeleton className="h-32" />
                    <Skeleton className="h-32" />
                    <Skeleton className="h-32" />
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Activity className="w-8 h-8 text-blue-600" />
                        Enhanced Analytics
                    </h1>
                    <p className="text-gray-600 mt-1">Time-series trends and activity heatmaps</p>
                </div>
                <div className="flex gap-2">
                    <Button onClick={downloadReport} variant="outline" className="border-blue-200 text-blue-700 hover:bg-blue-50">
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF report
                    </Button>
                    <Button onClick={fetchAnalytics} variant="outline">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Trend Indicators */}
            {trends && (
                <div className="grid gap-6 md:grid-cols-3">
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
                                Email Volume Trend
                                <HelpTooltip
                                    title="Volume Trend"
                                    description="Compares the number of emails classified in the last 7 days vs the previous 7 days. Helps track workload changes."
                                />
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-2xl font-bold">{trends.volume.recent}</div>
                                    <p className="text-xs text-gray-500">Last 7 days</p>
                                </div>
                                <div className={`flex items-center gap-1 px-2 py-1 rounded ${getTrendColor(trends.volume.trend)}`}>
                                    {getTrendIcon(trends.volume.trend)}
                                    <span className="text-sm font-semibold">{Math.abs(trends.volume.change_percent)}%</span>
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                vs {trends.volume.previous} (previous 7 days)
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
                                Avg Confidence Trend
                                <HelpTooltip
                                    title="Confidence Trend"
                                    description="Shows if the model's classifications are becoming more or less certain over time. Significant drops might indicate a need for retraining."
                                />
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-2xl font-bold">{(trends.confidence.recent * 100).toFixed(1)}%</div>
                                    <p className="text-xs text-gray-500">Last 7 days</p>
                                </div>
                                <div className={`flex items-center gap-1 px-2 py-1 rounded ${getTrendColor(trends.confidence.trend)}`}>
                                    {getTrendIcon(trends.confidence.trend)}
                                    <span className="text-sm font-semibold">{Math.abs(trends.confidence.change_percent)}%</span>
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                vs {(trends.confidence.previous * 100).toFixed(1)}% (previous 7 days)
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-gray-600">Category Trends</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-1 max-h-20 overflow-y-auto">
                                {Object.entries(trends.categories).slice(0, 3).map(([category, data]) => (
                                    <div key={category} className="flex items-center justify-between text-xs">
                                        <span className="font-medium truncate">{category}</span>
                                        <div className="flex items-center gap-1">
                                            {getTrendIcon(data.trend)}
                                            <span className={getTrendColor(data.trend).split(' ')[0]}>
                                                {Math.abs(data.change_percent)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Time-Series Line Chart */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-green-600" />
                        Email Volume Over Time (Last 30 Days)
                    </CardTitle>
                    <CardDescription>Daily email classification trends</CardDescription>
                </CardHeader>
                <CardContent>
                    {timeSeries.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={timeSeries}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="date" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} name="Emails" />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            No time-series data available
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Heatmap */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        🔥 Email Volume Heatmap
                        <HelpTooltip
                            title="Activity Heatmap"
                            description="Identifies peak periods of email activity. Useful for resource planning and understanding when most emails are received."
                        />
                    </CardTitle>
                    <CardDescription>
                        Email activity by day of week and hour of day (Last 30 days)
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {renderHeatmap()}
                </CardContent>
            </Card>

            {/* Category Distribution Over Time */}
            {Object.keys(categoryTimeSeries).length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Category Distribution Over Time</CardTitle>
                        <CardDescription>Top categories trending over the last 30 days</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {Object.entries(categoryTimeSeries).slice(0, 5).map(([category, dateData]) => {
                                const chartData = Object.entries(dateData).map(([date, count]) => ({
                                    date,
                                    count
                                })).reverse()

                                return (
                                    <div key={category} className="border rounded-lg p-3">
                                        <h4 className="font-semibold mb-2 capitalize">{category}</h4>
                                        <ResponsiveContainer width="100%" height={100}>
                                            <BarChart data={chartData}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="date" hide />
                                                <YAxis hide />
                                                <Tooltip />
                                                <Bar dataKey="count" fill="#8884d8" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

export default AnalyticsPage
