import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import {
    TrendingUp, TrendingDown, BarChart3, Target, Award,
    AlertCircle, RefreshCw, CheckCircle2, XCircle, Activity
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    PieChart, Pie, Cell
} from 'recharts'
import HelpTooltip from '@/components/shared/HelpTooltip'
import { Download, FileText } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PerformancePage = () => {
    const { token } = useAuth()
    const { toast } = useToast()

    const [loading, setLoading] = useState(true)
    const [summary, setSummary] = useState(null)
    const [confusionMatrix, setConfusionMatrix] = useState(null)
    const [categoryMetrics, setCategoryMetrics] = useState(null)
    const [misclassified, setMisclassified] = useState([])
    const [confidenceDist, setConfidenceDist] = useState(null)

    const fetchPerformanceData = async () => {
        setLoading(true)
        try {
            const [summaryRes, confusionRes, metricsRes, misclassifiedRes, confidenceRes] = await Promise.all([
                axios.get(`${API_URL}/api/performance/summary`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/performance/confusion-matrix`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/performance/metrics`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/performance/misclassified?limit=20`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/performance/confidence-distribution`, { headers: { Authorization: `Bearer ${token}` } })
            ])

            setSummary(summaryRes.data)
            setConfusionMatrix(confusionRes.data)
            setCategoryMetrics(metricsRes.data)
            setMisclassified(misclassifiedRes.data.misclassified_emails || [])
            setConfidenceDist(confidenceRes.data)
        } catch (error) {
            console.error('Error fetching performance data:', error)
            toast({
                title: "Error",
                description: "Failed to load performance metrics",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    const downloadReport = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/export/performance/pdf`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `performance_report_${new Date().toISOString().split('T')[0]}.pdf`)
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
        fetchPerformanceData()
    }, [])

    const getMetricColor = (value) => {
        if (value >= 90) return 'text-green-600'
        if (value >= 75) return 'text-blue-600'
        if (value >= 60) return 'text-yellow-600'
        return 'text-red-600'
    }

    const getMetricBadge = (value) => {
        if (value >= 90) return { color: 'bg-green-100 text-green-800', label: 'Excellent' }
        if (value >= 75) return { color: 'bg-blue-100 text-blue-800', label: 'Good' }
        if (value >= 60) return { color: 'bg-yellow-100 text-yellow-800', label: 'Fair' }
        return { color: 'bg-red-100 text-red-800', label: 'Needs Improvement' }
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

    // Prepare confusion matrix heatmap data
    const renderConfusionMatrixHeatmap = () => {
        if (!confusionMatrix || !confusionMatrix.matrix || confusionMatrix.total_corrections === 0) {
            return (
                <div className="text-center py-12 text-gray-500">
                    <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No user corrections available yet</p>
                    <p className="text-sm mt-2">Confusion matrix will appear once you start correcting email classifications</p>
                </div>
            )
        }

        const categories = confusionMatrix.categories
        const matrix = confusionMatrix.matrix

        return (
            <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                    <thead>
                        <tr>
                            <th className="border p-2 bg-gray-50 font-semibold">Actual →<br />Predicted ↓</th>
                            {categories.map(cat => (
                                <th key={cat} className="border p-2 bg-gray-50 font-semibold">{cat}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {categories.map(actualCat => (
                            <tr key={actualCat}>
                                <td className="border p-2 bg-gray-50 font-semibold">{actualCat}</td>
                                {categories.map(predCat => {
                                    const value = matrix[actualCat]?.[predCat] || 0
                                    const isCorrect = actualCat === predCat
                                    return (
                                        <td
                                            key={predCat}
                                            className={`border p-2 text-center ${value > 0
                                                ? isCorrect
                                                    ? 'bg-green-100 font-semibold'
                                                    : 'bg-red-50'
                                                : 'bg-white'
                                                }`}
                                        >
                                            {value || '-'}
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div className="mt-3 text-xs text-gray-600">
                    <p><span className="inline-block w-4 h-4 bg-green-100 border mr-1"></span> Correct predictions (diagonal)</p>
                    <p><span className="inline-block w-4 h-4 bg-red-50 border mr-1"></span> Misclassifications</p>
                </div>
            </div>
        )
    }

    // Prepare metrics table chart data
    const metricsTableData = categoryMetrics?.categories?.map(category => {
        const metrics = categoryMetrics.metrics[category]
        return {
            category,
            ...metrics
        }
    }) || []

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7c7c']

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <BarChart3 className="w-8 h-8 text-blue-600" />
                        Model Performance Dashboard
                    </h1>
                    <p className="text-gray-600 mt-1">ML classification evaluation metrics</p>
                </div>
                <div className="flex gap-2">
                    <Button onClick={downloadReport} variant="outline" className="border-blue-200 text-blue-700 hover:bg-blue-50">
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF report
                    </Button>
                    <Button onClick={fetchPerformanceData} variant="outline">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Key Metrics Cards */}
            <div className="grid gap-6 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
                            Overall Accuracy
                            <HelpTooltip
                                title="Overall Accuracy"
                                description="The percentage of emails that were correctly classified across all categories. It shows the general reliability of your model."
                            />
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-3xl font-bold ${getMetricColor(summary?.accuracy?.accuracy || 0)}`}>
                            {summary?.accuracy?.accuracy?.toFixed(1)}%
                        </div>
                        <Badge className={`mt-2 ${getMetricBadge(summary?.accuracy?.accuracy || 0).color}`}>
                            {getMetricBadge(summary?.accuracy?.accuracy || 0).label}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-2">
                            {summary?.accuracy?.correct || 0} correct / {summary?.accuracy?.total || 0} total
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
                            Weighted F1-Score
                            <HelpTooltip
                                title="F1-Score"
                                description="A balanced metric that considers both precision and recall. 'Weighted' means it accounts for categories with more or fewer emails. It's often more informative than accuracy for unbalanced data."
                            />
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-3xl font-bold ${getMetricColor(summary?.weighted_f1_score || 0)}`}>
                            {summary?.weighted_f1_score?.toFixed(1)}%
                        </div>
                        <Badge className={`mt-2 ${getMetricBadge(summary?.weighted_f1_score || 0).color}`}>
                            {getMetricBadge(summary?.weighted_f1_score || 0).label}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-2">
                            Harmonic mean of precision & recall
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">Avg Confidence</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                            {confidenceDist?.avg?.toFixed(1)}%
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                            Range: {confidenceDist?.min?.toFixed(0)}% - {confidenceDist?.max?.toFixed(0)}%
                        </p>
                        <p className="text-xs text-gray-500">
                            {confidenceDist?.total || 0} classifications
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-gray-600">User Corrections</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-orange-600">
                            {summary?.total_corrections || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                            Out of {summary?.total_classifications || 0} emails
                        </p>
                        <p className="text-xs text-gray-500">
                            {((summary?.total_corrections / (summary?.total_classifications || 1)) * 100).toFixed(1)}% correction rate
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Confusion Matrix */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Target className="w-5 h-5 text-purple-600" />
                        Confusion Matrix
                        <HelpTooltip
                            title="Confusion Matrix"
                            description="A heatmap showing where the model gets confused. The diagonal (green) shows correct predictions. Other cells (red) show exactly which categories are being mistaken for each other."
                        />
                    </CardTitle>
                    <CardDescription>
                        Visual representation of model predictions vs actual categories
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {renderConfusionMatrixHeatmap()}
                </CardContent>
            </Card>

            {/* Per-Category Performance */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Award className="w-5 h-5 text-blue-600" />
                        Per-Category Performance Metrics
                    </CardTitle>
                    <CardDescription>
                        Precision, Recall, and F1-Score for each category
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {metricsTableData.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left p-2 font-semibold">Category</th>
                                        <th className="text-right p-2 font-semibold">
                                            <div className="flex items-center justify-end gap-1">
                                                Precision
                                                <HelpTooltip
                                                    title="Precision"
                                                    description="Out of all emails the model labeled as this category, what percentage were actually correct? High precision means fewer 'False Alarms'."
                                                />
                                            </div>
                                        </th>
                                        <th className="text-right p-2 font-semibold">
                                            <div className="flex items-center justify-end gap-1">
                                                Recall
                                                <HelpTooltip
                                                    title="Recall"
                                                    description="Out of all actual emails in this category, what percentage did the model correctly find? High recall means fewer 'Missed Emails'."
                                                />
                                            </div>
                                        </th>
                                        <th className="text-right p-2 font-semibold">F1-Score</th>
                                        <th className="text-right p-2 font-semibold">Support</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {metricsTableData.map((row) => (
                                        <tr key={row.category} className="border-b hover:bg-gray-50">
                                            <td className="p-2 font-medium">{row.category}</td>
                                            <td className={`text-right p-2 ${getMetricColor(row.precision)}`}>
                                                {row.precision.toFixed(1)}%
                                            </td>
                                            <td className={`text-right p-2 ${getMetricColor(row.recall)}`}>
                                                {row.recall.toFixed(1)}%
                                            </td>
                                            <td className={`text-right p-2 ${getMetricColor(row.f1_score)}`}>
                                                {row.f1_score.toFixed(1)}%
                                            </td>
                                            <td className="text-right p-2 text-gray-600">
                                                {row.support}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            No performance metrics available yet. Start correcting email classifications to see metrics.
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Confidence Distribution */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="w-5 h-5 text-green-600" />
                            Confidence Distribution
                        </CardTitle>
                        <CardDescription>
                            Distribution of model confidence scores
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {confidenceDist && confidenceDist.bins ? (
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={confidenceDist.bins.map((bin, idx) => ({
                                    bin,
                                    count: confidenceDist.counts[idx]
                                }))}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="bin" />
                                    <YAxis />
                                    <Tooltip />
                                    <Bar dataKey="count" fill="#8884d8" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                No confidence data available
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Misclassified Emails */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <XCircle className="w-5 h-5 text-red-600" />
                            Recent Misclassifications
                        </CardTitle>
                        <CardDescription>
                            Emails that were corrected by users (last 20)
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {misclassified.length > 0 ? (
                            <div className="space-y-3 max-h-64 overflow-y-auto">
                                {misclassified.map((email) => (
                                    <div key={email.id} className="p-3 border rounded-lg text-sm">
                                        <div className="font-medium truncate">{email.subject}</div>
                                        <div className="text-xs text-gray-500 mt-1">{email.sender}</div>
                                        <div className="flex gap-2 mt-2">
                                            <Badge variant="outline" className="text-red-600 border-red-300">
                                                Predicted: {email.predicted}
                                            </Badge>
                                            <Badge variant="outline" className="text-green-600 border-green-300">
                                                Actual: {email.actual}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <CheckCircle2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                No misclassifications yet!
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default PerformancePage
