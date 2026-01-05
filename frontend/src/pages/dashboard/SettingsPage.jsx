import React, { useState } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Save, FileText, BrainCircuit, Bot } from 'lucide-react'

// Basic Tabs implementation if Shadcn tabs aren't available/installed yet
const SimpleTabs = ({ children, defaultValue }) => {
    const [activeTab, setActiveTab] = useState(defaultValue)
    return (
        <div className="space-y-4">
            <div className="flex space-x-2 border-b">
                {React.Children.map(children, child => {
                    if (child.type === SimpleTabsList) {
                        return React.cloneElement(child, { activeTab, setActiveTab })
                    }
                    return null
                })}
            </div>
            {React.Children.map(children, child => {
                if (child.type === SimpleTabsContent && child.props.value === activeTab) {
                    return child.props.children
                }
                return null
            })}
        </div>
    )
}

const SimpleTabsList = ({ children, activeTab, setActiveTab }) => (
    <div className="flex space-x-4">
        {React.Children.map(children, child => (
            <button
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === child.props.value
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
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
    const { API_URL, token } = useAuth()

    // Retraining State
    const [retraining, setRetraining] = useState(false)
    const [retrainingStatus, setRetrainingStatus] = useState(null)

    // Templates State
    const [template, setTemplate] = useState({ name: '', subject: '', body: '' })
    const [templateSubmitting, setTemplateSubmitting] = useState(false)

    // Reports State
    const [generatingReport, setGeneratingReport] = useState(false)

    // --- Actions ---

    const handleRetrain = async () => {
        if (!confirm('Start model retraining? This may take a while.')) return
        setRetraining(true)
        try {
            const response = await axios.post(`${API_URL}/api/ml/retrain?use_feedback=true`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            alert(response.data.message || 'Retraining started')
            fetchRetrainingStatus()
        } catch (err) {
            alert('Retraining failed: ' + err.message)
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
            console.error(err)
        }
    }

    const handleSaveTemplate = async (e) => {
        e.preventDefault()
        setTemplateSubmitting(true)
        try {
            await axios.post(`${API_URL}/api/auto-reply/templates`, template, {
                headers: { Authorization: `Bearer ${token}` }
            })
            alert('Template saved!')
            setTemplate({ name: '', subject: '', body: '' })
        } catch (err) {
            alert('Failed to save template: ' + err.message)
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

            alert(`Report generated with ${response.data.record_count} records`)
        } catch (err) {
            alert('Report generation failed')
        } finally {
            setGeneratingReport(false)
        }
    }

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Settings & Automation</h2>

            <SimpleTabs defaultValue="templates">
                <SimpleTabsList>
                    <SimpleTabsTrigger value="templates">Auto-Reply Templates</SimpleTabsTrigger>
                    <SimpleTabsTrigger value="model">AI Model</SimpleTabsTrigger>
                    <SimpleTabsTrigger value="reports">Reports</SimpleTabsTrigger>
                </SimpleTabsList>

                {/* Templates Tab */}
                <SimpleTabsContent value="templates">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Bot className="h-5 w-5" />
                                Create Auto-Reply Template
                            </CardTitle>
                            <CardDescription>Configure automated responses for specific scenarios.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSaveTemplate} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Template Name</Label>
                                    <Input
                                        placeholder="e.g. Out of Office"
                                        value={template.name}
                                        onChange={e => setTemplate({ ...template, name: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Subject Line</Label>
                                    <Input
                                        placeholder="Email subject"
                                        value={template.subject}
                                        onChange={e => setTemplate({ ...template, subject: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Body Content</Label>
                                    <Textarea
                                        placeholder="Message body..."
                                        className="min-h-[150px]"
                                        value={template.body}
                                        onChange={e => setTemplate({ ...template, body: e.target.value })}
                                        required
                                    />
                                </div>
                                <Button type="submit" disabled={templateSubmitting}>
                                    {templateSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    <Save className="mr-2 h-4 w-4" /> Save Template
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                </SimpleTabsContent>

                {/* AI Model Tab */}
                <SimpleTabsContent value="model">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <BrainCircuit className="h-5 w-5" />
                                Model Management
                            </CardTitle>
                            <CardDescription>Retrain the AI model using verified data and feedback.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="bg-muted p-4 rounded-lg">
                                <h4 className="font-semibold mb-2">Current Status</h4>
                                <p className="text-sm text-muted-foreground">
                                    {retrainingStatus ? JSON.stringify(retrainingStatus) : "Ready"}
                                </p>
                            </div>
                            <Button onClick={handleRetrain} disabled={retraining} variant="default">
                                {retraining && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Start Retraining
                            </Button>
                        </CardContent>
                    </Card>
                </SimpleTabsContent>

                {/* Reports Tab */}
                <SimpleTabsContent value="reports">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5" />
                                Generate Reports
                            </CardTitle>
                            <CardDescription>Export classification history and insights.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button onClick={handleGenerateReport} disabled={generatingReport}>
                                {generatingReport && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Download Classification Report
                            </Button>
                        </CardContent>
                    </Card>
                </SimpleTabsContent>
            </SimpleTabs>
        </div>
    )
}

export default SettingsPage
