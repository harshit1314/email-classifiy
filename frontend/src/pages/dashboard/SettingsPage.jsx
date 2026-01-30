import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Save, FileText, BrainCircuit, Bot, Settings as SettingsIcon, User, Bell, Shield, Sparkles, Download, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from "@/components/ui/use-toast"

// Basic Tabs implementation
const SimpleTabs = ({ children, defaultValue }) => {
    const [activeTab, setActiveTab] = useState(defaultValue)
    return (
        <div className="space-y-6">
            <div className="flex space-x-2 overflow-x-auto pb-2 border-b-2 border-gray-100">
                {React.Children.map(children, child => {
                    if (child.type === SimpleTabsList) {
                        return React.cloneElement(child, { activeTab, setActiveTab })
                    }
                    return null
                })}
            </div>
            <div className="animate-in fade-in duration-300">
                {React.Children.map(children, child => {
                    if (child.type === SimpleTabsContent && child.props.value === activeTab) {
                        return child.props.children
                    }
                    return null
                })}
            </div>
        </div>
    )
}

const SimpleTabsList = ({ children, activeTab, setActiveTab }) => (
    <div className="flex space-x-2">
        {React.Children.map(children, child => (
            <button
                className={cn(
                    "px-5 py-3 text-sm font-semibold rounded-t-lg transition-all duration-200 whitespace-nowrap",
                    activeTab === child.props.value
                        ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
                onClick={() => setActiveTab(child.props.value)}
            >
                {child.props.children}
            </button>
        ))}
    </div>
)
const SimpleTabsTrigger = ({ children, value }) => <div>{children}</div>
const SimpleTabsContent = ({ children, value }) => <div>{children}</div>


const SettingsPage = () => {
    const { API_URL, token, user } = useAuth()
    const { toast } = useToast()

    // Helper to format error messages safely
    const formatErrorMessage = (error) => {
        if (typeof error === 'string') return error
        if (Array.isArray(error)) {
            return error.map(e => e.msg || JSON.stringify(e)).join(', ')
        }
        if (error && typeof error === 'object') {
            return error.detail || error.message || JSON.stringify(error)
        }
        return 'An error occurred'
    }

    // Retraining State
    const [retraining, setRetraining] = useState(false)
    const [retrainingStatus, setRetrainingStatus] = useState(null)

    // Templates State
    const [template, setTemplate] = useState({ name: '', subject: '', body: '' })
    const [templateSubmitting, setTemplateSubmitting] = useState(false)

    // Reports State
    const [generatingReport, setGeneratingReport] = useState(false)

    // Profile State
    const [profile, setProfile] = useState({
        fullName: user?.full_name || '',
        email: user?.email || '',
        notifications: true,
        autoReply: false
    })
    const [savingProfile, setSavingProfile] = useState(false)

    useEffect(() => {
        if (user) {
            setProfile(prev => ({
                ...prev,
                fullName: user.full_name || '',
                email: user.email || ''
            }))
        }
        fetchRetrainingStatus()
    }, [user])

    // --- Actions ---

    const handleRetrain = async () => {
        if (!confirm('Start model retraining? This may take a while.')) return
        setRetraining(true)
        try {
            const response = await axios.post(`${API_URL}/api/ml/retrain?use_feedback=true`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            toast({
                title: "Retraining Started",
                description: response.data.message || "Model is being retrained with latest data",
            })
            fetchRetrainingStatus()
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Retraining Failed",
                description: formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message)
            })
        } finally {
            setRetraining(false)
        }
    }

    const fetchRetrainingStatus = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/ml/retraining-status`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setRetrainingStatus(response.data)
        } catch (err) {
            console.error('Failed to fetch retraining status:', err)
        }
    }

    const handleSaveTemplate = async (e) => {
        e.preventDefault()
        setTemplateSubmitting(true)
        try {
            await axios.post(`${API_URL}/api/auto-reply/templates`, template, {
                headers: { Authorization: `Bearer ${token}` }
            })
            toast({
                title: "Template Saved",
                description: "Your auto-reply template has been saved successfully",
            })
            setTemplate({ name: '', subject: '', body: '' })
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Failed to Save",
                description: formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message)
            })
        } finally {
            setTemplateSubmitting(false)
        }
    }

    const handleGenerateReport = async () => {
        setGeneratingReport(true)
        try {
            const response = await axios.post(`${API_URL}/api/reports/generate`, {
                report_type: 'classification',
                filters: { limit: 100 },
                format: 'text'
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            // Download logic
            const blob = new Blob([response.data.content], { type: 'text/plain' })
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `report_${Date.now()}.txt`
            link.click()

            toast({
                title: "Report Generated",
                description: `Downloaded report with ${response.data.record_count} records`,
            })
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Report Generation Failed",
                description: formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message)
            })
        } finally {
            setGeneratingReport(false)
        }
    }

    const handleSaveProfile = async (e) => {
        e.preventDefault()
        setSavingProfile(true)
        try {
            await axios.post(`${API_URL}/api/auth/settings`, {
                full_name: profile.fullName,
                notification_preferences: { enabled: profile.notifications },
                auto_reply_enabled: profile.autoReply
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            toast({
                title: "Settings Saved",
                description: "Your profile settings have been updated",
            })
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Failed to Save",
                description: formatErrorMessage(err.response?.data?.detail || err.response?.data || "Could not update settings")
            })
        } finally {
            setSavingProfile(false)
        }
    }

    return (
        <div className="flex-1 flex flex-col h-screen bg-transparent">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    <div>
                        <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-green-600 to-teal-600 bg-clip-text text-transparent mb-2">
                            Settings
                        </h2>
                        <p className="text-sm text-muted-foreground">Manage your account, automation, and AI preferences</p>
                    </div>

                    <SimpleTabs defaultValue="profile">
                        <SimpleTabsList>
                            <SimpleTabsTrigger value="profile">
                                <User className="mr-2 h-4 w-4 inline" />
                                Profile
                            </SimpleTabsTrigger>
                            <SimpleTabsTrigger value="templates">
                                <Bot className="mr-2 h-4 w-4 inline" />
                                Templates
                            </SimpleTabsTrigger>
                            <SimpleTabsTrigger value="model">
                                <BrainCircuit className="mr-2 h-4 w-4 inline" />
                                AI Model
                            </SimpleTabsTrigger>
                            <SimpleTabsTrigger value="reports">
                                <FileText className="mr-2 h-4 w-4 inline" />
                                Reports
                            </SimpleTabsTrigger>
                        </SimpleTabsList>

                        {/* Profile Tab */}
                        <SimpleTabsContent value="profile">
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-blue-500 to-purple-600 p-2">
                                            <User className="h-5 w-5 text-white" />
                                        </div>
                                        Profile Settings
                                    </CardTitle>
                                    <CardDescription>Update your personal information and preferences</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <form onSubmit={handleSaveProfile} className="space-y-6">
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold">Full Name</Label>
                                            <Input
                                                placeholder="John Doe"
                                                value={profile.fullName}
                                                onChange={e => setProfile({ ...profile, fullName: e.target.value })}
                                                className="h-11"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold">Email Address</Label>
                                            <Input
                                                type="email"
                                                value={profile.email}
                                                disabled
                                                className="h-11 bg-gray-50"
                                            />
                                            <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                                        </div>
                                        
                                        <div className="space-y-4 pt-4 border-t">
                                            <h4 className="font-semibold flex items-center gap-2">
                                                <Bell className="h-4 w-4" />
                                                Preferences
                                            </h4>
                                            <div className="flex items-center justify-between p-4 rounded-lg bg-blue-50 border border-blue-100">
                                                <div className="flex-1">
                                                    <p className="font-medium text-sm">Email Notifications</p>
                                                    <p className="text-xs text-muted-foreground">Receive alerts for classified emails</p>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => setProfile({ ...profile, notifications: !profile.notifications })}
                                                    className={cn(
                                                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                                                        profile.notifications ? "bg-blue-600" : "bg-gray-300"
                                                    )}
                                                >
                                                    <span
                                                        className={cn(
                                                            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                                                            profile.notifications ? "translate-x-6" : "translate-x-1"
                                                        )}
                                                    />
                                                </button>
                                            </div>
                                            <div className="flex items-center justify-between p-4 rounded-lg bg-purple-50 border border-purple-100">
                                                <div className="flex-1">
                                                    <p className="font-medium text-sm">Auto-Reply</p>
                                                    <p className="text-xs text-muted-foreground">Enable automatic responses</p>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => setProfile({ ...profile, autoReply: !profile.autoReply })}
                                                    className={cn(
                                                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                                                        profile.autoReply ? "bg-purple-600" : "bg-gray-300"
                                                    )}
                                                >
                                                    <span
                                                        className={cn(
                                                            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                                                            profile.autoReply ? "translate-x-6" : "translate-x-1"
                                                        )}
                                                    />
                                                </button>
                                            </div>
                                        </div>

                                        <Button 
                                            type="submit" 
                                            disabled={savingProfile}
                                            className="w-full h-11 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                                        >
                                            {savingProfile ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Saving...
                                                </>
                                            ) : (
                                                <>
                                                    <Save className="mr-2 h-4 w-4" />
                                                    Save Changes
                                                </>
                                            )}
                                        </Button>
                                    </form>
                                </CardContent>
                            </Card>
                        </SimpleTabsContent>

                        {/* Templates Tab */}
                        <SimpleTabsContent value="templates">
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-purple-500 to-pink-600 p-2">
                                            <Bot className="h-5 w-5 text-white" />
                                        </div>
                                        Auto-Reply Templates
                                    </CardTitle>
                                    <CardDescription>Create intelligent templates for automated email responses</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <form onSubmit={handleSaveTemplate} className="space-y-6">
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold">Template Name</Label>
                                            <Input
                                                placeholder="e.g., Customer Support Response"
                                                value={template.name}
                                                onChange={e => setTemplate({ ...template, name: e.target.value })}
                                                required
                                                className="h-11"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold">Subject Line</Label>
                                            <Input
                                                placeholder="e.g., Thank you for contacting us"
                                                value={template.subject}
                                                onChange={e => setTemplate({ ...template, subject: e.target.value })}
                                                required
                                                className="h-11"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-sm font-semibold">Message Body</Label>
                                            <Textarea
                                                placeholder="Enter your auto-reply message here..."
                                                value={template.body}
                                                onChange={e => setTemplate({ ...template, body: e.target.value })}
                                                rows={6}
                                                required
                                                className="resize-none"
                                            />
                                            <p className="text-xs text-muted-foreground">Use placeholders like {'{name}'} and {'{email}'}</p>
                                        </div>
                                        <Button 
                                            type="submit" 
                                            disabled={templateSubmitting}
                                            className="w-full h-11 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                                        >
                                            {templateSubmitting ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Saving Template...
                                                </>
                                            ) : (
                                                <>
                                                    <Save className="mr-2 h-4 w-4" />
                                                    Save Template
                                                </>
                                            )}
                                        </Button>
                                    </form>
                                </CardContent>
                            </Card>
                        </SimpleTabsContent>

                        {/* AI Model Tab */}
                        <SimpleTabsContent value="model">
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-green-500 to-emerald-600 p-2">
                                            <BrainCircuit className="h-5 w-5 text-white" />
                                        </div>
                                        AI Model Management
                                    </CardTitle>
                                    <CardDescription>Retrain and optimize your email classification model</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 p-6">
                                        <div className="flex items-start gap-4">
                                            <div className="rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 p-3">
                                                <Sparkles className="h-6 w-6 text-white" />
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-bold text-lg mb-2">Current Model Status</h4>
                                                <div className="space-y-2">
                                                    {retrainingStatus ? (
                                                        <div className="text-sm space-y-1">
                                                            <p className="flex items-center gap-2">
                                                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                                                <span className="text-gray-700">Status: <span className="font-medium">{retrainingStatus.status || 'Active'}</span></span>
                                                            </p>
                                                            <p className="text-gray-600">Last trained: {retrainingStatus.last_trained || 'Never'}</p>
                                                            <p className="text-gray-600">Accuracy: {retrainingStatus.accuracy || 'N/A'}</p>
                                                        </div>
                                                    ) : (
                                                        <p className="text-sm text-gray-600 flex items-center gap-2">
                                                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                                            Model is ready for retraining
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
                                        <p className="text-sm text-blue-900">
                                            <strong>Tip:</strong> Retraining improves classification accuracy by learning from your feedback and verified emails. This process may take several minutes.
                                        </p>
                                    </div>

                                    <Button 
                                        onClick={handleRetrain} 
                                        disabled={retraining}
                                        className="w-full h-12 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-lg"
                                    >
                                        {retraining ? (
                                            <>
                                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                                Retraining Model...
                                            </>
                                        ) : (
                                            <>
                                                <TrendingUp className="mr-2 h-5 w-5" />
                                                Start Retraining
                                            </>
                                        )}
                                    </Button>
                                </CardContent>
                            </Card>
                        </SimpleTabsContent>

                        {/* Reports Tab */}
                        <SimpleTabsContent value="reports">
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-orange-500 to-red-600 p-2">
                                            <FileText className="h-5 w-5 text-white" />
                                        </div>
                                        Analytics & Reports
                                    </CardTitle>
                                    <CardDescription>Export detailed classification insights and performance metrics</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="grid gap-4">
                                        <div className="rounded-xl bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200 p-6">
                                            <div className="flex items-start gap-4">
                                                <div className="rounded-lg bg-gradient-to-br from-orange-500 to-red-600 p-3">
                                                    <FileText className="h-6 w-6 text-white" />
                                                </div>
                                                <div className="flex-1">
                                                    <h4 className="font-bold text-lg mb-2">Classification Report</h4>
                                                    <p className="text-sm text-gray-600 mb-4">
                                                        Export a comprehensive report including email classifications, categories, confidence scores, and timestamps.
                                                    </p>
                                                    <ul className="text-sm text-gray-600 space-y-1 mb-4">
                                                        <li>• Last 100 classified emails</li>
                                                        <li>• Category distribution</li>
                                                        <li>• Classification accuracy metrics</li>
                                                        <li>• Text format (.txt)</li>
                                                    </ul>
                                                    <Button 
                                                        onClick={handleGenerateReport} 
                                                        disabled={generatingReport}
                                                        className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700"
                                                    >
                                                        {generatingReport ? (
                                                            <>
                                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                                Generating...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Download className="mr-2 h-4 w-4" />
                                                                Download Report
                                                            </>
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="rounded-xl bg-purple-50 border border-purple-200 p-4">
                                        <p className="text-sm text-purple-900">
                                            <strong>Note:</strong> Reports are generated in real-time and reflect the current state of your email classifications.
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        </SimpleTabsContent>
                    </SimpleTabs>
                </div>
            </div>
        </div>
    )
}

export default SettingsPage
