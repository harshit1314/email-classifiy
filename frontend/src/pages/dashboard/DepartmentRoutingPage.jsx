import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, Building2, Mail, Users, TrendingUp, Edit2, Check, X, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/use-toast"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from '@/components/ui/input'

const DepartmentRoutingPage = () => {
    const { API_URL, token } = useAuth()
    const { toast } = useToast()
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [departments, setDepartments] = useState([])
    const [departmentStats, setDepartmentStats] = useState({})
    const [categoryMappings, setCategoryMappings] = useState({})
    const [editingCategory, setEditingCategory] = useState(null)
    const [selectedDepartment, setSelectedDepartment] = useState('')
    const [editingEmail, setEditingEmail] = useState(null)
    const [emailInput, setEmailInput] = useState('')

    // Department colors matching the theme
    const DEPARTMENT_COLORS = {
        'Sales': '#EF4444',       // Red
        'HR': '#EC4899',          // Pink
        'Finance': '#10B981',     // Green
        'Support': '#3B82F6',     // Blue
        'Marketing': '#F59E0B',   // Amber
        'IT': '#8B5CF6',          // Purple
    }

    const getDepartmentColor = (dept) => DEPARTMENT_COLORS[dept] || '#6B7280'

    // Map display names back to keys for stats lookup
    const getDepartmentKey = (displayName) => {
        const mapping = {
            'Human Resources': 'HR',
            'Customer Support': 'Support',
            'IT/Admin': 'IT',
            'Sales': 'Sales',
            'Finance': 'Finance',
            'Marketing': 'Marketing'
        }
        return mapping[displayName] || displayName
    }

    const fetchData = async (isAutoRefresh = false) => {
        if (!isAutoRefresh) setLoading(true)
        setRefreshing(true)
        try {
            const [deptRes, statsRes, mappingsRes] = await Promise.all([
                axios.get(`${API_URL}/api/departments`),
                axios.get(`${API_URL}/api/analytics/by-department`),
                axios.get(`${API_URL}/api/departments/mappings`)
            ])

            setDepartments(deptRes.data.departments || [])
            setDepartmentStats(statsRes.data.department_statistics || {})
            setCategoryMappings(mappingsRes.data.mappings || {})
        } catch (err) {
            console.error('Failed to fetch department data:', err)
            toast({
                variant: "destructive",
                title: "Failed to fetch data",
                description: err.response?.data?.detail || "Could not load department information.",
            })
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    const updateCategoryMapping = async (category, newDepartment) => {
        try {
            // Use the key version for the API call
            const deptKey = getDepartmentKey(newDepartment)

            await axios.post(`${API_URL}/api/departments/mapping`, {
                category,
                department: deptKey
            })

            toast({
                title: "Mapping updated",
                description: `Category "${category}" now routes to ${newDepartment}`,
            })

            // Refresh data
            await fetchData(true)
            setEditingCategory(null)
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Update failed",
                description: err.response?.data?.detail || "Could not update mapping.",
            })
        }
    }

    const updateDepartmentEmail = async (deptKey, newEmail) => {
        try {
            await axios.put(
                `${API_URL}/api/departments/${deptKey}/email?email=${encodeURIComponent(newEmail)}`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
            )

            toast({
                title: "Forwarding email updated",
                description: `${deptKey} will now forward to ${newEmail}`,
            })

            // Refresh data to reflect the change
            await fetchData(true)
            setEditingEmail(null)
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Update failed",
                description: err.response?.data?.detail || "Could not update department email.",
            })
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    // Prepare chart data - use keys for stats lookup
    const barChartData = departments.map((dept) => {
        const key = getDepartmentKey(dept.name)
        const stats = departmentStats[key] || { total: 0 }
        return {
            name: dept.name,
            emails: stats.total || 0,
            fill: getDepartmentColor(key)
        }
    }).sort((a, b) => b.emails - a.emails)

    const pieChartData = departments.map((dept) => {
        const key = getDepartmentKey(dept.name)
        const stats = departmentStats[key] || { total: 0 }
        return {
            name: dept.name,
            value: stats.total || 0
        }
    }).filter(d => d.value > 0)

    const totalEmails = Object.values(departmentStats).reduce((sum, dept) => sum + (dept.total || 0), 0)

    return (
        <div className="flex-1 flex flex-col h-screen bg-transparent">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
                                Department Routing
                            </h2>
                            <p className="text-sm text-muted-foreground">Manage how emails are routed to departments</p>
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

                    {/* Summary Stats */}
                    <div className="grid gap-6 md:grid-cols-3">
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-blue-100">Total Departments</CardTitle>
                                <Building2 className="h-4 w-4 text-blue-100" />
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{departments.length}</div>
                                )}
                                <p className="text-xs text-blue-100">Active routing destinations</p>
                            </CardContent>
                        </Card>

                        <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-purple-100">Total Routed</CardTitle>
                                <Mail className="h-4 w-4 text-purple-100" />
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{totalEmails}</div>
                                )}
                                <p className="text-xs text-purple-100">Emails distributed</p>
                            </CardContent>
                        </Card>

                        <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-green-600 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
                                <CardTitle className="text-sm font-medium text-green-100">Category Mappings</CardTitle>
                                <Users className="h-4 w-4 text-green-100" />
                            </CardHeader>
                            <CardContent className="relative z-10">
                                {loading ? (
                                    <Skeleton className="h-8 w-16 mb-1 bg-white/20" />
                                ) : (
                                    <div className="text-3xl font-bold mb-1">{Object.keys(categoryMappings).length}</div>
                                )}
                                <p className="text-xs text-green-100">Configured routes</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Department Cards */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Departments Overview</h3>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {loading ? (
                                Array.from({ length: 6 }).map((_, i) => (
                                    <Card key={i} className="border-0 shadow-lg">
                                        <CardContent className="pt-6">
                                            <Skeleton className="h-6 w-32 mb-4" />
                                            <Skeleton className="h-4 w-full mb-2" />
                                            <Skeleton className="h-4 w-24" />
                                        </CardContent>
                                    </Card>
                                ))
                            ) : (
                                departments.map((dept) => {
                                    const deptKey = getDepartmentKey(dept.name)
                                    const stats = departmentStats[deptKey] || { total: 0, categories: {} }
                                    const percentage = totalEmails > 0
                                        ? ((stats.total / totalEmails) * 100).toFixed(1)
                                        : 0
                                    const color = getDepartmentColor(deptKey)

                                    return (
                                        <Card
                                            key={dept.name}
                                            className="group border-0 hover:shadow-xl transition-all duration-300 bg-white/90 backdrop-blur overflow-hidden relative"
                                            style={{ borderLeft: `4px solid ${color}` }}
                                        >
                                            <div
                                                className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-10 -translate-y-8 translate-x-8 group-hover:scale-150 transition-transform duration-500"
                                                style={{ backgroundColor: color }}
                                            ></div>
                                            <CardContent className="pt-6 relative z-10">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <div
                                                        className="w-3 h-3 rounded-full shadow-lg animate-pulse"
                                                        style={{ backgroundColor: color }}
                                                    />
                                                    <h4 className="font-semibold text-lg group-hover:text-blue-600 transition-colors">
                                                        {dept.name}
                                                    </h4>
                                                </div>

                                                <p className="text-sm text-muted-foreground mb-4 min-h-[40px]">
                                                    {dept.description}
                                                </p>

                                                <div className="flex items-center gap-2 text-sm mb-4">
                                                    <Mail className="h-4 w-4 text-muted-foreground" />
                                                    {editingEmail === deptKey ? (
                                                        <div className="flex items-center gap-1 flex-1">
                                                            <Input
                                                                value={emailInput}
                                                                onChange={(e) => setEmailInput(e.target.value)}
                                                                placeholder="department@gmail.com"
                                                                className="h-7 text-xs font-mono"
                                                                onKeyDown={(e) => {
                                                                    if (e.key === 'Enter') {
                                                                        updateDepartmentEmail(deptKey, emailInput)
                                                                    } else if (e.key === 'Escape') {
                                                                        setEditingEmail(null)
                                                                    }
                                                                }}
                                                                autoFocus
                                                            />
                                                            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => updateDepartmentEmail(deptKey, emailInput)}>
                                                                <Check className="h-3 w-3 text-green-600" />
                                                            </Button>
                                                            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setEditingEmail(null)}>
                                                                <X className="h-3 w-3 text-red-600" />
                                                            </Button>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-1 flex-1 cursor-pointer group/email" onClick={() => { setEditingEmail(deptKey); setEmailInput(dept.email || '') }}>
                                                            <span className={cn("font-mono text-xs", dept.email?.includes('@company.com') ? 'text-orange-500 italic' : 'text-muted-foreground')}>
                                                                {dept.email || 'Click to set email'}
                                                            </span>
                                                            <Edit2 className="h-3 w-3 text-muted-foreground opacity-0 group-hover/email:opacity-100 transition-opacity" />
                                                            {dept.email && !dept.email.includes('@company.com') && (
                                                                <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full ml-1">✓ Active</span>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="mb-3">
                                                    <div className="flex justify-between items-center mb-2">
                                                        <span className="text-2xl font-bold" style={{ color }}>
                                                            {stats.total}
                                                        </span>
                                                        <span className="text-xs text-muted-foreground font-medium">
                                                            {percentage}% of total
                                                        </span>
                                                    </div>

                                                    {/* Progress Bar */}
                                                    <div className="w-full bg-gray-100 rounded-full h-2 shadow-inner">
                                                        <div
                                                            className="h-2 rounded-full transition-all duration-500 shadow-sm"
                                                            style={{
                                                                width: `${percentage}%`,
                                                                backgroundColor: color
                                                            }}
                                                        />
                                                    </div>
                                                </div>

                                                {Object.keys(stats.categories || {}).length > 0 && (
                                                    <div className="text-xs text-muted-foreground">
                                                        <span className="font-semibold">Categories:</span>{' '}
                                                        {Object.keys(stats.categories).slice(0, 2).join(', ')}
                                                        {Object.keys(stats.categories).length > 2 && ` +${Object.keys(stats.categories).length - 2} more`}
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    )
                                })
                            )}
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="grid gap-6 md:grid-cols-2">
                        {/* Bar Chart */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Email Distribution</CardTitle>
                                <CardDescription>Emails by department (bar chart)</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {loading || barChartData.length === 0 ? (
                                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                                        {barChartData.length === 0 ? "No data available" : "Loading chart..."}
                                    </div>
                                ) : (
                                    <div className="h-64 w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={barChartData}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="name" />
                                                <YAxis />
                                                <Tooltip />
                                                <Bar dataKey="emails" radius={[8, 8, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Pie Chart */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Department Share</CardTitle>
                                <CardDescription>Percentage distribution</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {loading || pieChartData.length === 0 ? (
                                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                                        {pieChartData.length === 0 ? "No data available" : "Loading chart..."}
                                    </div>
                                ) : (
                                    <div className="h-64 w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={pieChartData}
                                                    cx="50%"
                                                    cy="50%"
                                                    labelLine={false}
                                                    label={({ name, percent }) => percent > 0.05 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''}
                                                    outerRadius={80}
                                                    fill="#8884d8"
                                                    dataKey="value"
                                                >
                                                    {pieChartData.map((entry) => (
                                                        <Cell key={entry.name} fill={getDepartmentColor(entry.name)} />
                                                    ))}
                                                </Pie>
                                                <Tooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Category Mappings */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Category Mappings</CardTitle>
                            <CardDescription>Configure which categories route to which departments</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {loading ? (
                                    Array.from({ length: 6 }).map((_, i) => (
                                        <Skeleton key={i} className="h-12 w-full" />
                                    ))
                                ) : (
                                    Object.entries(categoryMappings)
                                        .sort(([a], [b]) => a.localeCompare(b))
                                        .map(([category, department]) => (
                                            <div
                                                key={category}
                                                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                                            >
                                                <div className="flex items-center gap-3 flex-1">
                                                    <div
                                                        className="w-2 h-2 rounded-full"
                                                        style={{ backgroundColor: getDepartmentColor(department) }}
                                                    />
                                                    <span className="font-medium">{category.replace(/_/g, ' ')}</span>
                                                    <span className="text-muted-foreground text-sm">→</span>
                                                </div>

                                                {editingCategory === category ? (
                                                    <div className="flex items-center gap-2">
                                                        <Select
                                                            value={selectedDepartment}
                                                            onValueChange={setSelectedDepartment}
                                                        >
                                                            <SelectTrigger className="w-[180px]">
                                                                <SelectValue placeholder="Select department" />
                                                            </SelectTrigger>
                                                            <SelectContent>
                                                                {departments.map(dept => (
                                                                    <SelectItem key={dept.name} value={dept.name}>
                                                                        {dept.name}
                                                                    </SelectItem>
                                                                ))}
                                                            </SelectContent>
                                                        </Select>
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            onClick={() => updateCategoryMapping(category, selectedDepartment)}
                                                        >
                                                            <Check className="h-4 w-4" />
                                                        </Button>
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            onClick={() => setEditingCategory(null)}
                                                        >
                                                            <X className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-2">
                                                        <span
                                                            className="font-semibold px-3 py-1 rounded-full text-sm"
                                                            style={{
                                                                backgroundColor: `${getDepartmentColor(department)}20`,
                                                                color: getDepartmentColor(department)
                                                            }}
                                                        >
                                                            {department}
                                                        </span>
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            onClick={() => {
                                                                setEditingCategory(category)
                                                                setSelectedDepartment(department)
                                                            }}
                                                        >
                                                            <Edit2 className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        ))
                                )}
                            </div>
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    )
}

export default DepartmentRoutingPage
