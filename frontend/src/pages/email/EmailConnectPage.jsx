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
    const [gmailCredentials, setGmailCredentials] = useState({ client_id: '', client_secret: '', interval: 30, batch_size: 20 })
    const [gmailConnecting, setGmailConnecting] = useState(false)
    const [showInstructions, setShowInstructions] = useState(false)

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
            await axios.post(`${API_URL}/api/email/start-gmail`, {
                client_id: gmailCredentials.client_id,
                client_secret: gmailCredentials.client_secret,
                interval: parseInt(gmailCredentials.interval),
                batch_size: parseInt(gmailCredentials.batch_size)
            })
            alert('Gmail polling started! Check your browser for OAuth authorization.')
            fetchEmailPollingStatus()
        } catch (err) {
            alert('Failed to start Gmail polling: ' + (err.response?.data?.detail || err.message))
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
                <h2 className="text-3xl font-bold tracking-tight">Connect Email</h2>
                <Button variant="outline" onClick={fetchEmailPollingStatus} disabled={loading}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh Status
                </Button>
            </div>

            {/* Credentials Instructions Accordion */}
            <Card className="bg-blue-50 border-blue-200">
                <CardHeader className="pb-2 cursor-pointer" onClick={() => setShowInstructions(!showInstructions)}>
                    <CardTitle className="text-base font-medium text-blue-800 flex items-center justify-between">
                        <span className="flex items-center gap-2">
                            <HelpCircle className="h-5 w-5" />
                            How to get Gmail Client ID & Secret
                        </span>
                        {showInstructions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </CardTitle>
                </CardHeader>
                {showInstructions && (
                    <CardContent className="text-sm text-blue-900 space-y-2 pt-0">
                        <ol className="list-decimal pl-5 space-y-1 mt-2">
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
                <Card className={emailPollingStatus?.gmail_connected ? "border-green-500 shadow-md" : ""}>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Mail className={`h-5 w-5 ${emailPollingStatus?.gmail_connected ? 'text-green-600' : 'text-red-500'}`} />
                            Gmail Integration
                        </CardTitle>
                        <CardDescription>Connect your Gmail account using OAuth2</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {emailPollingStatus?.gmail_connected ? (
                            <div className="flex flex-col items-center justify-center py-8 space-y-6">
                                <Button
                                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-6 px-8 rounded-full shadow-lg transform transition-all hover:scale-105 pointer-events-none"
                                >
                                    <CheckCircle2 className="mr-2 h-6 w-6" />
                                    GMAIL CONNECTED
                                </Button>
                                <div className="text-center space-y-1">
                                    <p className="font-medium text-lg">Polling Active</p>
                                    <p className="text-sm text-muted-foreground">
                                        Last Check: {emailPollingStatus.last_check_gmail ? new Date(emailPollingStatus.last_check_gmail).toLocaleTimeString() : 'Just now'}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Limit: {emailPollingStatus.batch_size || 20} emails/poll
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleStartGmail} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Client ID</Label>
                                    <Input
                                        value={gmailCredentials.client_id}
                                        onChange={(e) => setGmailCredentials({ ...gmailCredentials, client_id: e.target.value })}
                                        placeholder="OAuth Client ID"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Client Secret</Label>
                                    <Input
                                        type="password"
                                        value={gmailCredentials.client_secret}
                                        onChange={(e) => setGmailCredentials({ ...gmailCredentials, client_secret: e.target.value })}
                                        placeholder="OAuth Client Secret"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Poll Interval (seconds)</Label>
                                        <Input
                                            type="number"
                                            value={gmailCredentials.interval}
                                            onChange={(e) => setGmailCredentials({ ...gmailCredentials, interval: e.target.value })}
                                            min="10"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Emails to Fetch (Limit)</Label>
                                        <div className="relative">
                                            <Input
                                                type="number"
                                                value={gmailCredentials.batch_size}
                                                onChange={(e) => setGmailCredentials({ ...gmailCredentials, batch_size: e.target.value })}
                                                min="1"
                                                max="500"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>
                                <Button className="w-full" type="submit" disabled={gmailConnecting}>
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

                <Card className="opacity-70">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Mail className="h-5 w-5 text-gray-400" />
                            Outlook Integration
                        </CardTitle>
                        <CardDescription>Connect via Microsoft Graph API</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="py-12 flex flex-col items-center justify-center text-center">
                            <p className="text-muted-foreground mb-4">Outlook integration is currently disabled.</p>
                            <Button variant="secondary" disabled>Coming Soon</Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default EmailConnectPage
