import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
    Loader2, Copy, ExternalLink, X, Sparkles, AlertTriangle, AlertCircle,
    Clock, CheckCircle, Smile, Frown, Meh, Heart, Zap, Mail, Phone,
    DollarSign, Calendar, User, Building2, Hash, MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'

const EmailDetailModal = ({ isOpen, onClose, emailId, emailData }) => {
    const { API_URL, token } = useAuth()
    const [email, setEmail] = useState(emailData || null)
    const [loading, setLoading] = useState(isOpen && emailId && !emailData)
    const [error, setError] = useState(null)
    const [copied, setCopied] = useState(false)

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

    // Analysis state
    const [analysis, setAnalysis] = useState(null)
    const [analyzing, setAnalyzing] = useState(false)
    const [analysisError, setAnalysisError] = useState(null)

    // Smart reply state
    const [smartReply, setSmartReply] = useState(null)
    const [generatingReply, setGeneratingReply] = useState(false)
    const [replyCopied, setReplyCopied] = useState(false)

    useEffect(() => {
        // If we have emailData already, use it immediately
        if (emailData) {
            setEmail(emailData)
            setLoading(false)
            setError(null)
            return
        }

        // Otherwise, fetch if modal is open and we have an ID
        if (isOpen && emailId) {
            fetchEmailDetails(emailId)
        }
    }, [isOpen, emailId, emailData])

    const getEmailField = (field) => {
        // Handle both naming conventions from API and dashboard
        if (!email) return undefined
        // Try exact field name first
        if (email[field] !== undefined) return email[field]
        // Try with email_ prefix
        if (email[`email_${field}`] !== undefined) return email[`email_${field}`]
        return undefined
    }

    const formatConfidence = (confidence) => {
        if (!confidence && confidence !== 0) return "0"
        // If confidence is already a percentage (100 or greater), return as is
        // If it's a decimal (0-1), multiply by 100
        const value = parseFloat(confidence)
        if (value > 1) {
            return value.toFixed(1)
        } else {
            return (value * 100).toFixed(1)
        }
    }

    // Perform full analysis on the email
    const performAnalysis = async () => {
        if (!email) return

        setAnalyzing(true)
        setAnalysisError(null)
        try {
            const response = await axios.post(`${API_URL}/api/analyze/full`, {
                subject: getEmailField('subject') || '',
                body: getEmailField('body') || '',
                sender: getEmailField('sender') || ''
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setAnalysis(response.data)
        } catch (err) {
            setAnalysisError(formatErrorMessage(err.response?.data?.detail || err.response?.data || 'Analysis failed'))
            console.error('Analysis error:', err)
        } finally {
            setAnalyzing(false)
        }
    }

    // Generate smart reply
    const generateSmartReply = async () => {
        if (!email) return

        setGeneratingReply(true)
        try {
            const response = await axios.post(`${API_URL}/api/replies/generate`, {
                subject: getEmailField('subject') || '',
                body: getEmailField('body') || '',
                sender: getEmailField('sender') || ''
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSmartReply(response.data)
        } catch (err) {
            console.error('Reply generation error:', err)
        } finally {
            setGeneratingReply(false)
        }
    }

    const copyReplyToClipboard = () => {
        if (!smartReply) return
        const text = `Subject: ${smartReply.subject}\n\n${smartReply.body}`
        navigator.clipboard.writeText(text)
        setReplyCopied(true)
        setTimeout(() => setReplyCopied(false), 2000)
    }

    // Priority styling
    const getPriorityStyle = (priority) => {
        const styles = {
            critical: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: AlertTriangle },
            high: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300', icon: AlertCircle },
            normal: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300', icon: Clock },
            low: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300', icon: CheckCircle }
        }
        return styles[priority?.toLowerCase()] || styles.normal
    }

    // Sentiment styling
    const getSentimentStyle = (sentiment) => {
        const styles = {
            positive: { bg: 'bg-green-100', text: 'text-green-800', icon: Smile, emoji: '😊' },
            negative: { bg: 'bg-red-100', text: 'text-red-800', icon: Frown, emoji: '😠' },
            neutral: { bg: 'bg-gray-100', text: 'text-gray-600', icon: Meh, emoji: '😐' },
            mixed: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Heart, emoji: '🤔' }
        }
        return styles[sentiment?.toLowerCase()] || styles.neutral
    }

    // Entity icons
    const entityIcons = {
        emails: Mail,
        phones: Phone,
        money: DollarSign,
        dates: Calendar,
        names: User,
        companies: Building2,
        order_numbers: Hash
    }

    const fetchEmailDetails = async (id) => {
        setLoading(true)
        setError(null)
        try {
            const response = await axios.get(`${API_URL}/api/email/details/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            console.log('Fetched email details:', response.data)
            setEmail(response.data)
        } catch (err) {
            setError(formatErrorMessage(err.response?.data?.detail || err.response?.data || 'Failed to fetch email details'))
            console.error('Error fetching email details:', err)
        } finally {
            setLoading(false)
        }
    }

    const getConfidenceColor = (confidence) => {
        if (confidence >= 0.8) return "bg-green-100 text-green-800 border-green-300"
        if (confidence >= 0.5) return "bg-yellow-100 text-yellow-800 border-yellow-300"
        return "bg-red-100 text-red-800 border-red-300"
    }

    const getCategoryColor = (category) => {
        const colors = {
            "spam": "bg-red-100 text-red-800",
            "important": "bg-blue-100 text-blue-800",
            "promotion": "bg-orange-100 text-orange-800",
            "social": "bg-purple-100 text-purple-800",
            "updates": "bg-green-100 text-green-800",
            "support_request": "bg-indigo-100 text-indigo-800",
            "sales_inquiry": "bg-cyan-100 text-cyan-800",
            "billing_issue": "bg-amber-100 text-amber-800",
            "general_feedback": "bg-lime-100 text-lime-800"
        }
        return colors[category?.toLowerCase()] || "bg-gray-100 text-gray-800"
    }

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    if (!isOpen) return null

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        <span>Email Details</span>
                        <button
                            onClick={onClose}
                            className="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </DialogTitle>
                    <DialogDescription>
                        View full email classification details and analysis
                    </DialogDescription>
                </DialogHeader>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                ) : email ? (
                    <div className="space-y-6">
                        {/* Email Header */}
                        <Card className="border-t-4 border-t-blue-500 shadow-md">
                            <CardHeader className="bg-gradient-to-br from-blue-50/50 to-indigo-50/50">
                                <CardTitle className="text-lg break-words font-semibold text-gray-900">{getEmailField('subject') || '(No Subject)'}</CardTitle>
                                <div className="flex items-center justify-between mt-4">
                                    <div className="space-y-1 flex-1">
                                        <p className="text-sm text-muted-foreground">
                                            <span className="font-semibold">From:</span> {getEmailField('sender') || 'Unknown Sender'}
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            <span className="font-semibold">Date:</span> {new Date(getEmailField('timestamp') || Date.now()).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            </CardHeader>
                        </Card>

                        {/* Classification Results */}
                        <Card className="border-l-4 border-l-emerald-500 shadow-md">
                            <CardHeader className="bg-gradient-to-br from-emerald-50/50 to-teal-50/50">
                                <CardTitle className="text-sm font-semibold text-gray-900">Classification Results</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-2">Category</p>
                                        <Badge className={cn("text-sm py-1 px-3", getCategoryColor(getEmailField('category')))}>
                                            {getEmailField('category') || 'Unknown'}
                                        </Badge>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-2">Confidence</p>
                                        <Badge className={cn("text-sm py-1 px-3 border", getConfidenceColor(getEmailField('confidence')))}>
                                            {formatConfidence(getEmailField('confidence'))}%
                                        </Badge>
                                    </div>
                                </div>

                                {/* Confidence Bar */}
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase font-semibold mb-2">Model Certainty</p>
                                    <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 transition-all"
                                            style={{ width: `${parseFloat(getEmailField('confidence') || 0) > 1 ? getEmailField('confidence') : (getEmailField('confidence') || 0) * 100}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Additional Classification Info */}
                                {getEmailField('department') && (
                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Department</p>
                                        <p className="text-sm font-medium">{getEmailField('department')}</p>
                                    </div>
                                )}

                                {getEmailField('sentiment') && (
                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Sentiment</p>
                                        <Badge variant="outline">{getEmailField('sentiment')}</Badge>
                                    </div>
                                )}

                                {/* Classification Explanation */}
                                {getEmailField('explanation') && (
                                    <div className="mt-4 p-3 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-md shadow-sm">
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-2">Classification Details</p>
                                        <p className="text-sm text-blue-900 leading-relaxed">{email.explanation}</p>
                                    </div>
                                )}

                                {getEmailField('urgency') && (
                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Urgency</p>
                                        <Badge variant={getEmailField('urgency') === 'high' ? 'destructive' : 'secondary'}>
                                            {getEmailField('urgency')}
                                        </Badge>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* AI Analysis Section */}
                        <Card className="border-purple-300 border-l-4 shadow-lg bg-gradient-to-br from-purple-50 via-pink-50 to-fuchsia-50">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm flex items-center gap-2 font-semibold text-purple-900">
                                        <Sparkles className="h-5 w-5 text-purple-600" />
                                        AI Analysis
                                    </CardTitle>
                                    <Button
                                        size="sm"
                                        variant={analysis ? "outline" : "default"}
                                        onClick={performAnalysis}
                                        disabled={analyzing}
                                        className={cn(!analysis && "bg-purple-600 hover:bg-purple-700")}
                                    >
                                        {analyzing ? (
                                            <>
                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                                Analyzing...
                                            </>
                                        ) : analysis ? (
                                            <>
                                                <Zap className="mr-2 h-3 w-3" />
                                                Re-analyze
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="mr-2 h-3 w-3" />
                                                Analyze Email
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </CardHeader>

                            {analysisError && (
                                <CardContent>
                                    <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                                        {analysisError}
                                    </div>
                                </CardContent>
                            )}

                            {analysis && (
                                <CardContent className="space-y-4">
                                    {/* Priority */}
                                    {analysis.priority && (
                                        <div className="space-y-2">
                                            <p className="text-xs text-muted-foreground uppercase font-semibold">Priority Level</p>
                                            <div className="flex items-center gap-2">
                                                {(() => {
                                                    const style = getPriorityStyle(analysis.priority.level)
                                                    const Icon = style.icon
                                                    return (
                                                        <>
                                                            <Badge className={cn("text-sm py-1 px-3 border", style.bg, style.text, style.border)}>
                                                                <Icon className="h-3 w-3 mr-1" />
                                                                {analysis.priority.level?.toUpperCase()}
                                                            </Badge>
                                                            <span className="text-xs text-muted-foreground">
                                                                ({(analysis.priority.confidence * 100).toFixed(0)}% confidence)
                                                            </span>
                                                        </>
                                                    )
                                                })()}
                                            </div>
                                            {analysis.priority.recommendation && (
                                                <p className="text-xs text-muted-foreground italic">
                                                    {analysis.priority.recommendation}
                                                </p>
                                            )}
                                            {analysis.priority.indicators?.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {analysis.priority.indicators.slice(0, 3).map((ind, i) => (
                                                        <span key={i} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                                                            {ind}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Sentiment */}
                                    {analysis.sentiment && (
                                        <div className="space-y-2">
                                            <p className="text-xs text-muted-foreground uppercase font-semibold">Sentiment Analysis</p>
                                            <div className="flex items-center gap-2">
                                                {(() => {
                                                    const style = getSentimentStyle(analysis.sentiment.sentiment)
                                                    const Icon = style.icon
                                                    return (
                                                        <>
                                                            <Badge className={cn("text-sm py-1 px-3", style.bg, style.text)}>
                                                                <span className="mr-1">{style.emoji}</span>
                                                                {analysis.sentiment.sentiment?.toUpperCase()}
                                                            </Badge>
                                                            <span className="text-xs text-muted-foreground">
                                                                ({(analysis.sentiment.confidence * 100).toFixed(0)}% confidence)
                                                            </span>
                                                        </>
                                                    )
                                                })()}
                                            </div>
                                            {analysis.sentiment.summary && (
                                                <p className="text-xs text-muted-foreground italic">
                                                    {analysis.sentiment.summary}
                                                </p>
                                            )}
                                            {analysis.sentiment.emotions && Object.keys(analysis.sentiment.emotions).length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {Object.entries(analysis.sentiment.emotions)
                                                        .filter(([_, v]) => v)
                                                        .slice(0, 4)
                                                        .map(([emotion, _]) => (
                                                            <span key={emotion} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                                                                {emotion}
                                                            </span>
                                                        ))}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Entities */}
                                    {analysis.entities && analysis.entities.total_entities > 0 && (
                                        <div className="space-y-2">
                                            <p className="text-xs text-muted-foreground uppercase font-semibold">
                                                Extracted Entities ({analysis.entities.total_entities})
                                            </p>
                                            <div className="grid grid-cols-1 gap-2">
                                                {Object.entries(analysis.entities)
                                                    .filter(([key, val]) =>
                                                        !['total_entities', 'summary'].includes(key) &&
                                                        Array.isArray(val) && val.length > 0
                                                    )
                                                    .map(([type, values]) => {
                                                        const Icon = entityIcons[type] || Hash
                                                        return (
                                                            <div key={type} className="flex items-start gap-2 bg-white/60 rounded p-2">
                                                                <Icon className="h-4 w-4 text-purple-500 mt-0.5" />
                                                                <div className="flex-1">
                                                                    <span className="text-xs font-semibold capitalize text-gray-700">
                                                                        {type.replace('_', ' ')}:
                                                                    </span>
                                                                    <div className="flex flex-wrap gap-1 mt-1">
                                                                        {values.slice(0, 5).map((val, i) => {
                                                                            // Handle both string values and object values with 'value' key
                                                                            const displayValue = typeof val === 'object' && val !== null
                                                                                ? (val.value || JSON.stringify(val))
                                                                                : String(val)
                                                                            return (
                                                                                <span key={i} className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                                                                    {displayValue}
                                                                                </span>
                                                                            )
                                                                        })}
                                                                        {values.length > 5 && (
                                                                            <span className="text-xs text-muted-foreground">
                                                                                +{values.length - 5} more
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )
                                                    })}
                                            </div>
                                            {analysis.entities.summary && analysis.entities.summary.key_entities && (
                                                <p className="text-xs text-muted-foreground mt-2">
                                                    Key entities: {analysis.entities.summary.key_entities.join(', ')}
                                                </p>
                                            )}
                                        </div>
                                    )}
                                </CardContent>
                            )}

                            {!analysis && !analyzing && !analysisError && (
                                <CardContent>
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        Click "Analyze Email" to get AI-powered insights including priority detection, sentiment analysis, and entity extraction.
                                    </p>
                                </CardContent>
                            )}
                        </Card>

                        {/* Smart Reply Section */}
                        <Card className="border-amber-300 border-l-4 shadow-lg bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm flex items-center gap-2 font-semibold text-amber-900">
                                        <MessageSquare className="h-5 w-5 text-amber-600" />
                                        Smart Reply
                                    </CardTitle>
                                    <Button
                                        size="sm"
                                        variant={smartReply ? "outline" : "default"}
                                        onClick={generateSmartReply}
                                        disabled={generatingReply}
                                        className={cn(!smartReply && "bg-yellow-600 hover:bg-yellow-700")}
                                    >
                                        {generatingReply ? (
                                            <>
                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                                Generating...
                                            </>
                                        ) : smartReply ? (
                                            <>
                                                <Zap className="mr-2 h-3 w-3" />
                                                Regenerate
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="mr-2 h-3 w-3" />
                                                Generate Reply
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </CardHeader>

                            {smartReply ? (
                                <CardContent className="space-y-3">
                                    {/* Analysis Summary */}
                                    {smartReply.analysis && (
                                        <div className="flex flex-wrap gap-2 p-3 bg-white/70 rounded-lg shadow-sm">
                                            <Badge className="text-xs bg-blue-100 text-blue-800 border-blue-200">
                                                Dept: {smartReply.analysis.department}
                                            </Badge>
                                            <Badge className={cn("text-xs",
                                                smartReply.analysis.priority === 'critical' ? "bg-red-100 text-red-800 border-red-200" :
                                                    smartReply.analysis.priority === 'high' ? "bg-orange-100 text-orange-800 border-orange-200" :
                                                        "bg-gray-100 text-gray-600 border-gray-200"
                                            )}>
                                                Priority: {smartReply.analysis.priority}
                                            </Badge>
                                            <Badge className={cn("text-xs",
                                                smartReply.analysis.sentiment === 'positive' ? "bg-green-100 text-green-800 border-green-200" :
                                                    smartReply.analysis.sentiment === 'negative' ? "bg-red-100 text-red-800 border-red-200" :
                                                        "bg-gray-100 text-gray-600 border-gray-200"
                                            )}>
                                                Tone: {smartReply.analysis.sentiment}
                                            </Badge>
                                        </div>
                                    )}

                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Subject</p>
                                        <p className="text-sm font-medium bg-white/60 p-2 rounded">{smartReply.subject}</p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">Reply Body</p>
                                        <div className="text-sm bg-white/60 p-3 rounded whitespace-pre-wrap max-h-48 overflow-y-auto">
                                            {smartReply.body}
                                        </div>
                                    </div>

                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={copyReplyToClipboard}
                                        className="w-full"
                                    >
                                        {replyCopied ? (
                                            <>
                                                <CheckCircle className="mr-2 h-3 w-3 text-green-600" />
                                                Copied!
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="mr-2 h-3 w-3" />
                                                Copy to Clipboard
                                            </>
                                        )}
                                    </Button>
                                </CardContent>
                            ) : (
                                <CardContent>
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        Click "Generate Reply" to create an AI-powered response based on email analysis.
                                    </p>
                                </CardContent>
                            )}
                        </Card>

                        {/* Email Body */}
                        <Card className="border-l-4 border-l-slate-500 shadow-md">
                            <CardHeader className="bg-gradient-to-br from-slate-50/50 to-gray-50/50">
                                <CardTitle className="text-sm font-semibold text-gray-900">Email Body</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-muted/50 p-4 rounded-lg border border-border max-h-64 overflow-y-auto whitespace-pre-wrap text-sm text-foreground shadow-inner">
                                    {getEmailField('body') || '(No body content)'}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Probabilities */}
                        {(getEmailField('probabilities') && Object.keys(getEmailField('probabilities') || {}).length > 0) && (
                            <Card className="border-l-4 border-l-indigo-500 shadow-md">
                                <CardHeader className="bg-gradient-to-br from-indigo-50/50 to-violet-50/50">
                                    <CardTitle className="text-sm font-semibold text-gray-900">Category Probabilities</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    {(() => {
                                        const probs = getEmailField('probabilities') || {}
                                        const entries = Object.entries(probs)

                                        // Check if probabilities are valid (sum close to 100)
                                        const sum = entries.reduce((acc, [_, val]) => acc + (parseFloat(val) > 1 ? parseFloat(val) : parseFloat(val) * 100), 0)
                                        const isValid = sum > 90 && sum < 110

                                        // If invalid, normalize them
                                        let normalizedProbs = probs
                                        if (!isValid && entries.length > 0) {
                                            // Treat as softmax scores and normalize
                                            const maxVal = Math.max(...entries.map(([_, v]) => parseFloat(v)))
                                            const scores = entries.map(([cat, val]) => ({
                                                cat,
                                                score: Math.exp(parseFloat(val) - maxVal)
                                            }))
                                            const totalScore = scores.reduce((acc, { score }) => acc + score, 0)
                                            normalizedProbs = {}
                                            scores.forEach(({ cat, score }) => {
                                                normalizedProbs[cat] = (score / totalScore) * 100
                                            })
                                        }

                                        return Object.entries(normalizedProbs).map(([category, prob]) => {
                                            const value = parseFloat(prob)
                                            const displayValue = isValid && value > 1 ? value : (isValid ? value : value)
                                            const barWidth = Math.max(0, Math.min(displayValue, 100))

                                            return (
                                                <div key={category}>
                                                    <div className="flex justify-between text-sm mb-1">
                                                        <span className="font-medium capitalize">{category}</span>
                                                        <span className="text-muted-foreground">{displayValue.toFixed(1)}%</span>
                                                    </div>
                                                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-primary"
                                                            style={{ width: `${barWidth}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            )
                                        })
                                    })()}
                                </CardContent>
                            </Card>
                        )}

                        {/* Entities */}
                        {email.entities && Object.keys(email.entities).length > 0 && (
                            <Card className="border-l-4 border-l-cyan-500 shadow-md">
                                <CardHeader className="bg-gradient-to-br from-cyan-50/50 to-sky-50/50">
                                    <CardTitle className="text-sm font-semibold text-gray-900">Extracted Entities</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {Object.entries(getEmailField('entities') || {}).map(([entityType, values]) => (
                                        <div key={entityType}>
                                            <p className="text-xs text-muted-foreground uppercase font-semibold mb-1">
                                                {entityType}
                                            </p>
                                            <p className="text-sm">
                                                {Array.isArray(values) ? values.map(v =>
                                                    typeof v === 'object' ? (v.original || v.value || v.parsed || JSON.stringify(v)) : v
                                                ).join(', ') : String(values)}
                                            </p>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        )}

                        {/* Email Metadata */}
                        {getEmailField('id') && (
                            <Card className="border-l-4 border-l-gray-500 shadow-md">
                                <CardHeader className="bg-gradient-to-br from-gray-50/50 to-slate-50/50">
                                    <CardTitle className="text-sm font-semibold text-gray-900">Email ID</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center justify-between bg-muted p-3 rounded-lg shadow-sm">
                                        <code className="text-xs text-muted-foreground">{getEmailField('id')}</code>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => copyToClipboard(getEmailField('id'))}
                                        >
                                            <Copy className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    {copied && <p className="text-xs text-green-600 mt-2">Copied!</p>}
                                </CardContent>
                            </Card>
                        )}
                    </div>
                ) : (
                    <div className="text-center py-8 text-muted-foreground">
                        No email data available
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}

export default EmailDetailModal
