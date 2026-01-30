import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Mail, RefreshCw, CheckCircle2, Trash2, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react'

const EmailConnectPage = () => {
    const { API_URL, token } = useAuth()
    const [emailPollingStatus, setEmailPollingStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [gmailCredentials, setGmailCredentials] = useState({ client_id: '', client_secret: '', interval: 30, batch_size: 200 })
    const [gmailConnecting, setGmailConnecting] = useState(false)
    const [showInstructions, setShowInstructions] = useState(false)

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

    const fetchEmailPollingStatus = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/email/status`)
            setEmailPollingStatus(response.data)
        } catch (err) {
            console.error('Failed to fetch polling status:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchEmailPollingStatus()
        const interval = setInterval(fetchEmailPollingStatus, 3000)
        return () => clearInterval(interval)
    }, [])

    const handleStartGmail = async (e) => {
        e.preventDefault()
        if (!gmailCredentials.client_id || !gmailCredentials.client_secret) return
        setGmailConnecting(true)
        try {
            const resp = await axios.post(`${API_URL}/api/email/start-gmail`, {
                client_id: gmailCredentials.client_id,
                client_secret: gmailCredentials.client_secret,
                interval: parseInt(gmailCredentials.interval),
                batch_size: parseInt(gmailCredentials.batch_size)
            })
            const backfilled = resp.data?.backfilled ?? 0
            alert(`Gmail polling started! Backfilled ${backfilled} emails. Check your browser for OAuth authorization.`)
            fetchEmailPollingStatus()
        } catch (err) {
            alert('Failed to start Gmail polling: ' + formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message))
        } finally {
            setGmailConnecting(false)
        }
    }

    const handleDisconnectGmail = async () => {
        if (!confirm('Disconnect Gmail?')) return
        try {
            await axios.post(`${API_URL}/api/email/disconnect-gmail`)
            fetchEmailPollingStatus()
            // Reload to clear state
            window.location.reload()
        } catch (err) {
            alert('Failed to disconnect: ' + err.message)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Connect Email</h2>
                <Button variant="outline" onClick={fetchEmailPollingStatus} disabled={loading}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh Status
                </Button>
            </div>

            {/* Credentials Instructions Accordion */}
            <Card className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-l-4 border-l-blue-500 shadow-lg">
                <CardHeader className="pb-2 cursor-pointer" onClick={() => setShowInstructions(!showInstructions)}>
                    <CardTitle className="text-base font-semibold text-blue-900 flex items-center justify-between">
                        <span className="flex items-center gap-2">
                            <HelpCircle className="h-5 w-5" />
                            How to get Gmail Client ID & Secret
                        </span>
                        {showInstructions ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                    </CardTitle>
                </CardHeader>
                {showInstructions && (
                    <CardContent className="text-sm text-blue-900 space-y-2 pt-2">
                        <ol className="list-decimal pl-5 space-y-2 mt-2 leading-relaxed">
                            <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" className="underline font-semibold">Google Cloud Console</a>.</li>
                            <li>Create a new project or select an existing one.</li>
                            <li>Enable the <strong>Gmail API</strong> in "APIs & Services" &gt; "Library".</li>
                            <li>Go to "APIs & Services" &gt; "Credentials".</li>
                            <li>Click <strong>Create Credentials</strong> &gt; <strong>OAuth client ID</strong>.</li>
                            <li>Select <strong>Desktop app</strong> (or Web application if preferred).</li>
                            <li>Copy the <strong>Client ID</strong> and <strong>Client Secret</strong>.</li>
                            <li><strong>Important:</strong> If you get a "redirect_uri_mismatch" error, ensure you add <code>http://localhost</code> to "Authorized redirect URIs" in the console.</li>
                        </ol>
                    </CardContent>
                )}
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className={emailPollingStatus?.gmail_connected ? "border-l-4 border-l-green-500 shadow-xl bg-gradient-to-br from-green-50/50 to-emerald-50/50" : "border-l-4 border-l-gray-400 shadow-md"}>
                    <CardHeader className={emailPollingStatus?.gmail_connected ? "bg-gradient-to-r from-green-50/70 to-emerald-50/70" : "bg-gradient-to-r from-gray-50 to-slate-50"}>
                        <CardTitle className="flex items-center gap-2 font-semibold text-gray-900">
                            <Mail className={`h-6 w-6 ${emailPollingStatus?.gmail_connected ? 'text-green-600' : 'text-gray-500'}`} />
                            Gmail Integration
                        </CardTitle>
                        <CardDescription className="text-gray-700">Connect your Gmail account using OAuth2</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {emailPollingStatus?.gmail_connected ? (
                            <div className="flex flex-col items-center justify-center py-8 space-y-6">
                                <div className="relative">
                                    <div className="absolute inset-0 bg-green-400 blur-xl opacity-30 animate-pulse"></div>
                                    <Button
                                        className="relative bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-6 px-8 rounded-full shadow-lg transform transition-all pointer-events-none"
                                    >
                                        <CheckCircle2 className="mr-2 h-6 w-6" />
                                        GMAIL CONNECTED
                                    </Button>
                                </div>
                                <div className="text-center space-y-2 bg-white/60 p-4 rounded-lg shadow-sm">
                                    <p className="font-semibold text-lg text-gray-900">Polling Active</p>
                                    <p className="text-sm text-gray-700">
                                        Last Check: {emailPollingStatus.last_check_gmail ? new Date(emailPollingStatus.last_check_gmail).toLocaleTimeString() : 'Just now'}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Limit: {emailPollingStatus.batch_size || 200} emails/poll
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleStartGmail} className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="font-semibold text-gray-700">Client ID</Label>
                                    <Input
                                        value={gmailCredentials.client_id}
                                        onChange={(e) => setGmailCredentials({ ...gmailCredentials, client_id: e.target.value })}
                                        placeholder="OAuth Client ID"
                                        className="border-gray-300 focus:border-blue-500"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="font-semibold text-gray-700">Client Secret</Label>
                                    <Input
                                        type="password"
                                        value={gmailCredentials.client_secret}
                                        onChange={(e) => setGmailCredentials({ ...gmailCredentials, client_secret: e.target.value })}
                                        placeholder="OAuth Client Secret"
                                        className="border-gray-300 focus:border-blue-500"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="font-semibold text-gray-700">Poll Interval (seconds)</Label>
                                        <Input
                                            type="number"
                                            value={gmailCredentials.interval}
                                            onChange={(e) => setGmailCredentials({ ...gmailCredentials, interval: e.target.value })}
                                            min="10"
                                            className="border-gray-300 focus:border-blue-500"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="font-semibold text-gray-700">Emails to Fetch (Limit)</Label>
                                        <div className="relative">
                                            <Input
                                                type="number"
                                                value={gmailCredentials.batch_size}
                                                onChange={(e) => setGmailCredentials({ ...gmailCredentials, batch_size: e.target.value })}
                                                min="1"
                                                max="500"
                                                className="border-gray-300 focus:border-blue-500"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>
                                <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold shadow-lg" type="submit" disabled={gmailConnecting}>
                                    {gmailConnecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Connect Gmail
                                </Button>
                            </form>
                        )}
                    </CardContent>
                    {emailPollingStatus?.gmail_connected && (
                        <CardFooter>
                            <Button variant="destructive" className="w-full" onClick={handleDisconnectGmail}>
                                <Trash2 className="mr-2 h-4 w-4" /> Disconnect
                            </Button>
                        </CardFooter>
                    )}
                </Card>

                <Card className="opacity-80 border-l-4 border-l-gray-300 shadow-md bg-gradient-to-br from-gray-50 to-slate-100">
                    <CardHeader className="bg-gradient-to-r from-gray-50/70 to-slate-50/70">
                        <CardTitle className="flex items-center gap-2 font-semibold text-gray-700">
                            <Mail className="h-6 w-6 text-gray-400" />
                            Outlook Integration
                        </CardTitle>
                        <CardDescription className="text-gray-600">Connect via Microsoft Graph API</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
                            <div className="bg-gray-100 p-4 rounded-lg">
                                <Mail className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                                <p className="text-muted-foreground mb-4 font-medium">Outlook integration is currently disabled.</p>
                            </div>
                            <Button variant="secondary" disabled className="bg-gray-200 text-gray-500 cursor-not-allowed">Coming Soon</Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default EmailConnectPage
