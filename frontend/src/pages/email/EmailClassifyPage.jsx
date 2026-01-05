import React, { useState } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Send, Tag, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

const EmailClassifyPage = () => {
    const { API_URL } = useAuth()
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const [email, setEmail] = useState({
        subject: '',
        body: '',
        sender: ''
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const response = await axios.post(`${API_URL}/api/process/classify`, {
                subject: email.subject,
                body: email.body,
                sender: email.sender || undefined
            })
            setResult(response.data)
        } catch (err) {
            setError(err.response?.data?.detail || 'Classification failed')
        } finally {
            setLoading(false)
        }
    }

    const getConfidenceColor = (confidence) => {
        if (confidence >= 0.8) return "text-green-600 bg-green-50 border-green-200"
        if (confidence >= 0.5) return "text-yellow-600 bg-yellow-50 border-yellow-200"
        return "text-red-600 bg-red-50 border-red-200"
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Classify Email</h2>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Input Email</CardTitle>
                        <CardDescription>Paste email content to test the classifier</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label>Sender (Optional)</Label>
                                <Input
                                    placeholder="e.g. boss@company.com"
                                    value={email.sender}
                                    onChange={e => setEmail({ ...email, sender: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Subject</Label>
                                <Input
                                    placeholder="Email Subject"
                                    value={email.subject}
                                    onChange={e => setEmail({ ...email, subject: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Body</Label>
                                <Textarea
                                    placeholder="Paste email body here..."
                                    className="min-h-[200px]"
                                    value={email.body}
                                    onChange={e => setEmail({ ...email, body: e.target.value })}
                                    required
                                />
                            </div>
                            <Button type="submit" className="w-full" disabled={loading}>
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Analyze Email
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    {error && (
                        <Card className="border-red-200 bg-red-50">
                            <CardContent className="pt-6 text-red-600 flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5" />
                                {error}
                            </CardContent>
                        </Card>
                    )}

                    {result && (
                        <Card className="border-primary/20 bg-primary/5">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Tag className="h-5 w-5 text-primary" />
                                    Classification Result
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-2">
                                    <Label>Predicted Category</Label>
                                    <div className="text-3xl font-bold capitalize text-primary">
                                        {result.category}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label>Confidence Score</Label>
                                    <div className={cn("inline-flex items-center px-3 py-1 rounded-full border text-sm font-medium", getConfidenceColor(result.confidence))}>
                                        {(result.confidence * 100).toFixed(1)}%
                                    </div>
                                </div>

                                {result.explanation && (
                                    <div className="space-y-2">
                                        <Label>Explanation</Label>
                                        <p className="text-sm text-muted-foreground p-3 bg-background rounded-md border">
                                            {result.explanation}
                                        </p>
                                    </div>
                                )}

                                {result.urgency && (
                                    <div className="space-y-2">
                                        <Label>Urgency</Label>
                                        <div className={cn("inline-flex px-2 py-1 rounded border text-xs capitalize",
                                            result.urgency === 'high' ? 'bg-red-100 text-red-700 border-red-200' : 'bg-gray-100 text-gray-700 border-gray-200'
                                        )}>
                                            {result.urgency}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    )
}

export default EmailClassifyPage
