import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from '@/components/ui/button'
import { Loader2, Mail, Calendar, Tag, Sparkles, Copy, Check, X, Send, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from "@/components/ui/use-toast"
import { Textarea } from "@/components/ui/textarea"
import { Label } from '@/components/ui/label'

const EmailDetailModal = ({ isOpen, onClose, emailId, emailData, onDelete }) => {
    const { API_URL, token } = useAuth()
    const { toast } = useToast()
    const [email, setEmail] = useState(emailData || null)
    const [loading, setLoading] = useState(false)
    const [replyDraft, setReplyDraft] = useState(null)
    const [generatingReply, setGeneratingReply] = useState(false)
    const [copied, setCopied] = useState(false)
    const [forwarding, setForwarding] = useState(false)
    const [deleting, setDeleting] = useState(false)

    const getCategoryColor = (category) => {
        const colors = {
            sales: "bg-emerald-100 text-emerald-800 border border-emerald-200",
            finance: "bg-amber-100 text-amber-800 border border-amber-200",
            hr: "bg-pink-100 text-pink-800 border border-pink-200",
            marketing: "bg-violet-100 text-violet-800 border border-violet-200",
            it: "bg-cyan-100 text-cyan-800 border border-cyan-200",
            spam: "bg-red-100 text-red-800 border border-red-200",
            customer_support: "bg-indigo-100 text-indigo-800 border border-indigo-200"
        }
        return colors[category?.toLowerCase()] || "bg-gray-100 text-gray-800"
    }

    useEffect(() => {
        // If emailData is provided, use it directly
        if (emailData) {
            setEmail(emailData)
            return
        }

        // Otherwise, fetch if modal is open and we have an ID
        if (isOpen && emailId && !emailData) {
            fetchEmailDetails()
        }
    }, [isOpen, emailId, emailData])

    const fetchEmailDetails = async () => {
        setLoading(true)
        try {
            const response = await axios.get(`${API_URL}/api/emails/${emailId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setEmail(response.data)
        } catch (err) {
            console.error('Failed to fetch email details:', err)
            toast({
                variant: "destructive",
                title: "Failed to load email",
                description: "Could not fetch email details.",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleGenerateReply = async () => {
        setGeneratingReply(true)
        try {
            const response = await axios.post(`${API_URL}/api/replies/generate`,
                { classification_id: email.id },
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setReplyDraft(response.data)
            setCopied(false)
        } catch (err) {
            console.error("Failed to generate reply:", err)
            toast({
                variant: "destructive",
                title: "Failed to generate reply",
                description: "Could not generate AI reply.",
            })
        } finally {
            setGeneratingReply(false)
        }
    }

    const copyToClipboard = () => {
        if (!replyDraft) return
        const text = `Subject: ${replyDraft.subject}\n\n${replyDraft.body}`
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const handleClose = () => {
        setReplyDraft(null)
        setCopied(false)
        onClose()
    }

    const handleForward = async () => {
        if (!email?.id) return
        setForwarding(true)
        try {
            const response = await axios.post(
                `${API_URL}/api/departments/forward?classification_id=${email.id}`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
            )
            toast({
                title: "Email Forwarded",
                description: `Forwarded to ${response.data.forwarded_to}`,
            })
            // Update email data locally
            setEmail(prev => ({ ...prev, forwarded_to: response.data.forwarded_to }))
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Forwarding Failed",
                description: err.response?.data?.detail || "Could not forward email.",
            })
        } finally {
            setForwarding(false)
        }
    }

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-2xl">
                        <Mail className="h-6 w-6 text-blue-600" />
                        Email Details
                    </DialogTitle>
                    <DialogDescription>
                        Complete email information and classification details
                    </DialogDescription>
                </DialogHeader>

                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        <span className="ml-2 text-muted-foreground">Loading email details...</span>
                    </div>
                ) : email ? (
                    <div className="space-y-6">
                        {/* Email Header */}
                        <div className="space-y-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100">
                            <div>
                                <Label className="text-xs text-muted-foreground uppercase">Subject</Label>
                                <h3 className="text-xl font-semibold mt-1">
                                    {email.subject || email.email_subject || '(No Subject)'}
                                </h3>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-xs text-muted-foreground uppercase">From</Label>
                                    <p className="text-sm font-medium mt-1 flex items-center gap-2">
                                        <Mail className="h-4 w-4 text-blue-600" />
                                        {email.sender || email.email_sender || 'Unknown'}
                                    </p>
                                </div>

                                <div>
                                    <Label className="text-xs text-muted-foreground uppercase">Received</Label>
                                    <p className="text-sm font-medium mt-1 flex items-center gap-2">
                                        <Calendar className="h-4 w-4 text-purple-600" />
                                        {email.received_at ? new Date(email.received_at).toLocaleString() : 'Unknown'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Classification Info */}
                        <div className="space-y-3 p-4 bg-white rounded-lg border">
                            <h4 className="font-semibold flex items-center gap-2">
                                <Tag className="h-5 w-5 text-purple-600" />
                                Classification
                            </h4>

                            <div className="flex flex-wrap gap-3">
                                {email.category && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">Category:</span>
                                        <span className={cn("text-sm px-3 py-1.5 rounded-full font-bold shadow-sm", getCategoryColor(email.category))}>
                                            {email.category.replace(/_/g, ' ').toUpperCase()}
                                        </span>
                                    </div>
                                )}

                                {email.confidence && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">Confidence:</span>
                                        <span className="text-sm px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold shadow-sm">
                                            {(email.confidence > 1 ? email.confidence : email.confidence * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                )}

                                {email.department && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">Department:</span>
                                        <span className="text-sm px-3 py-1.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 font-semibold shadow-sm">
                                            🏢 {email.department}
                                        </span>
                                    </div>
                                )}

                                {email.forwarded_to && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">Forwarded to:</span>
                                        <span className="text-sm px-3 py-1.5 rounded-full bg-green-50 text-green-700 border border-green-200 font-semibold shadow-sm">
                                            ✉️ {email.forwarded_to}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Forward to Department */}
                            <div className="flex items-center gap-2 pt-2 border-t">
                                <Button
                                    onClick={handleForward}
                                    disabled={forwarding}
                                    size="sm"
                                    variant="outline"
                                    className="text-xs"
                                >
                                    {forwarding ? (
                                        <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> Forwarding...</>
                                    ) : (
                                        <><Send className="mr-1 h-3 w-3" /> {email.forwarded_to ? 'Re-forward' : 'Forward to Department'}</>
                                    )}
                                </Button>
                                {email.forwarded_to && (
                                    <span className="text-xs text-muted-foreground">Last sent to {email.forwarded_to}</span>
                                )}
                            </div>
                        </div>

                        {/* Email Body */}
                        <div className="space-y-2">
                            <Label className="text-sm font-semibold">Email Body</Label>
                            <div className="p-4 bg-gray-50 rounded-lg border max-h-96 overflow-y-auto">
                                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                                    {email.body || email.email_body || 'No body content'}
                                </p>
                            </div>
                        </div>

                        {/* Entities */}
                        {(email.entities?.dates?.length > 0 || email.entities?.money?.length > 0 || email.entities?.names?.length > 0 || email.entities?.emails?.length > 0 || email.entities?.phones?.length > 0 || email.entities?.order_numbers?.length > 0) && (
                            <div className="space-y-3 p-4 bg-purple-50 rounded-lg border border-purple-100">
                                <h4 className="font-semibold text-purple-900">Extracted Entities</h4>
                                <div className="flex flex-wrap gap-2">
                                    {email.entities?.dates?.map((date, i) => (
                                        <span key={`date-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200 font-medium">
                                            📅 {typeof date === 'object' ? (date.original || date.parsed) : date}
                                        </span>
                                    ))}
                                    {email.entities?.money?.map((amount, i) => (
                                        <span key={`amt-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-green-100 text-green-800 border border-green-200 font-medium">
                                            💰 {typeof amount === 'object' ? (amount.original || `$${amount.value}`) : amount}
                                        </span>
                                    ))}
                                    {email.entities?.names?.map((person, i) => (
                                        <span key={`person-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200 font-medium">
                                            👤 {typeof person === 'object' ? person.value : person}
                                        </span>
                                    ))}
                                    {email.entities?.emails?.map((emailEntity, i) => (
                                        <span key={`email-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 font-medium">
                                            ✉️ {typeof emailEntity === 'object' ? emailEntity.value : emailEntity}
                                        </span>
                                    ))}
                                    {email.entities?.phones?.map((phone, i) => (
                                        <span key={`phone-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200 font-medium">
                                            📞 {typeof phone === 'object' ? phone.value : phone}
                                        </span>
                                    ))}
                                    {email.entities?.order_numbers?.map((order, i) => (
                                        <span key={`order-${i}`} className="text-xs px-3 py-1.5 rounded-full bg-orange-100 text-orange-800 border border-orange-200 font-medium">
                                            🔖 {typeof order === 'object' ? order.value : order}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Smart Reply Section */}
                        <div className="space-y-3 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg border border-yellow-200">
                            <div className="flex items-center justify-between">
                                <h4 className="font-semibold flex items-center gap-2 text-orange-900">
                                    <Sparkles className="h-5 w-5 text-yellow-600" />
                                    AI Smart Reply
                                </h4>
                                {!replyDraft && (
                                    <Button
                                        onClick={handleGenerateReply}
                                        disabled={generatingReply}
                                        size="sm"
                                        className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600"
                                    >
                                        {generatingReply ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Generating...
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="mr-2 h-4 w-4" />
                                                Generate Reply
                                            </>
                                        )}
                                    </Button>
                                )}
                            </div>

                            {replyDraft && (
                                <div className="space-y-3 mt-4">
                                    {/* Analysis Summary */}
                                    {replyDraft.analysis && (
                                        <div className="flex flex-wrap gap-2 p-3 bg-white/80 rounded-lg">
                                            <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800 font-medium">
                                                📁 {replyDraft.analysis.department}
                                            </span>
                                            <span className={cn("text-xs px-2 py-1 rounded font-medium",
                                                replyDraft.analysis.priority === 'critical' ? "bg-red-100 text-red-800" :
                                                    replyDraft.analysis.priority === 'high' ? "bg-orange-100 text-orange-800" :
                                                        "bg-gray-100 text-gray-600"
                                            )}>
                                                ⚡ {replyDraft.analysis.priority}
                                            </span>
                                            <span className={cn("text-xs px-2 py-1 rounded font-medium",
                                                replyDraft.analysis.sentiment === 'positive' ? "bg-green-100 text-green-800" :
                                                    replyDraft.analysis.sentiment === 'negative' ? "bg-red-100 text-red-800" :
                                                        "bg-gray-100 text-gray-600"
                                            )}>
                                                {replyDraft.analysis.sentiment === 'positive' ? '😊' :
                                                    replyDraft.analysis.sentiment === 'negative' ? '😠' : '😐'} {replyDraft.analysis.sentiment}
                                            </span>
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <Label className="text-xs">Subject</Label>
                                        <div className="p-2 bg-white rounded border text-sm font-medium">
                                            {replyDraft.subject}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label className="text-xs">Body</Label>
                                        <Textarea
                                            value={replyDraft.body}
                                            readOnly
                                            className="h-[200px] bg-white"
                                        />
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            onClick={copyToClipboard}
                                            className="flex-1"
                                            variant="default"
                                        >
                                            {copied ? (
                                                <>
                                                    <Check className="h-4 w-4 mr-2" />
                                                    Copied!
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="h-4 w-4 mr-2" />
                                                    Copy to Clipboard
                                                </>
                                            )}
                                        </Button>
                                        <Button
                                            onClick={() => setReplyDraft(null)}
                                            variant="outline"
                                        >
                                            <X className="h-4 w-4 mr-2" />
                                            Clear
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex justify-between pt-4 border-t">
                            <Button
                                onClick={async () => {
                                    if (!window.confirm('Delete this email? It will also be moved to Gmail Trash.')) return
                                    setDeleting(true)
                                    try {
                                        await axios.delete(
                                            `${API_URL}/api/emails/${email.id}`,
                                            { headers: { Authorization: `Bearer ${token}` } }
                                        )
                                        toast({ title: "Email Deleted", description: "Moved to Gmail Trash" })
                                        if (onDelete) onDelete(email.id)
                                        handleClose()
                                    } catch (err) {
                                        toast({ variant: "destructive", title: "Delete Failed", description: err.response?.data?.detail || err.message })
                                    } finally {
                                        setDeleting(false)
                                    }
                                }}
                                variant="outline"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                                disabled={deleting}
                            >
                                {deleting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
                                Delete
                            </Button>
                            <Button onClick={handleClose} variant="outline">
                                Close
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-12 text-muted-foreground">
                        <p>No email data available</p>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}

export default EmailDetailModal
