import React, { useState, useEffect, Suspense, lazy } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { RefreshCw, Search, Filter, Loader2, Sparkles, Copy, Check, X } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/use-toast"
import { Calendar as CalendarIcon } from 'lucide-react'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

// Lazy load EmailDetailModal
const EmailDetailModal = lazy(() => import('@/components/EmailDetailModal'))

const EmailsPage = () => {
    const { API_URL, token } = useAuth()
    const { toast } = useToast()
    const [loading, setLoading] = useState(true)
    const [allClassifications, setAllClassifications] = useState([])
    const [unclassifiedEmails, setUnclassifiedEmails] = useState([])
    const [selectedEmail, setSelectedEmail] = useState(null)
    const [detailModalOpen, setDetailModalOpen] = useState(false)
    const [activeTab, setActiveTab] = useState('classified')
    const [selectedCategory, setSelectedCategory] = useState('all')
    const [stats, setStats] = useState({
        category_breakdown: {}
    })
    
    // Search & Filter State
    const [searchQuery, setSearchQuery] = useState('')
    const [showFilters, setShowFilters] = useState(false)
    const [searchResults, setSearchResults] = useState(null)
    const [sender, setSender] = useState('')
    const [dateRange, setDateRange] = useState({ from: undefined, to: undefined })
    const [minConfidence, setMinConfidence] = useState([0])
    const [replyDraft, setReplyDraft] = useState(null)
    const [generatingReply, setGeneratingReply] = useState(null)
    const [copied, setCopied] = useState(false)
    const [isSearching, setIsSearching] = useState(false)

    const fetchData = async () => {
        setLoading(true)
        try {
            const [classRes, unclassRes, statsRes] = await Promise.all([
                axios.get(`${API_URL}/api/dashboard/classifications?limit=1000`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/dashboard/unclassified`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { emails: [] } })),
                axios.get(`${API_URL}/api/dashboard/statistics`, { headers: { Authorization: `Bearer ${token}` } })
            ])

            // Calculate category breakdown from classifications
            const categories = {}
            let classifiedCount = 0
            
            classRes.data.classifications?.forEach(email => {
                if (email.category) {
                    categories[email.category] = (categories[email.category] || 0) + 1
                    classifiedCount += 1
                }
            })

            setStats({
                category_breakdown: categories,
                classified_count: classifiedCount
            })
            setAllClassifications(classRes.data.classifications || [])
            setUnclassifiedEmails(unclassRes.data.emails || [])
        } catch (err) {
            console.error('Failed to fetch emails:', err)
            toast({
                variant: "destructive",
                title: "Failed to load emails",
                description: "Could not fetch emails from backend.",
            })
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = async (e) => {
        e?.preventDefault()
        
        // Check if any filter is active
        const hasFilters = searchQuery.trim() || sender || dateRange.from || dateRange.to || minConfidence[0] > 0
        
        if (!hasFilters) {
            setSearchResults(null)
            return
        }

        setIsSearching(true)
        try {
            const params = {}
            
            // Add filters only if they have values
            if (searchQuery.trim()) {
                params.query = searchQuery.trim()
            }
            if (sender) {
                params.sender = sender
            }
            if (dateRange.from) {
                params.start_date = dateRange.from.toISOString()
            }
            if (dateRange.to) {
                params.end_date = dateRange.to.toISOString()
            }
            if (minConfidence[0] > 0) {
                params.min_confidence = minConfidence[0] / 100
            }
            
            params.limit = 100

            const response = await axios.get(`${API_URL}/api/search`, {
                params,
                headers: { Authorization: `Bearer ${token}` }
            })
            setSearchResults(response.data.results || [])
            
            if (response.data.results && response.data.results.length === 0) {
                toast({
                    title: "No results found",
                    description: "Try adjusting your filters.",
                })
            }
        } catch (err) {
            console.error('Search failed:', err)
            toast({
                variant: "destructive",
                title: "Search failed",
                description: err.response?.data?.detail || "Could not perform search.",
            })
        } finally {
            setIsSearching(false)
        }
    }

    const handleGenerateReply = async (email) => {
        setGeneratingReply(email.id)
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
            setGeneratingReply(null)
        }
    }

    const copyToClipboard = () => {
        if (!replyDraft) return
        const text = `Subject: ${replyDraft.subject}\n\n${replyDraft.body}`
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const clearSearch = () => {
        setSearchQuery('')
        setSender('')
        setDateRange({ from: undefined, to: undefined })
        setMinConfidence([0])
        setSearchResults(null)
    }

    const handleEmailClick = (email) => {
        setSelectedEmail(email)
        setDetailModalOpen(true)
    }

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 10000) // Refresh every 10s
        return () => clearInterval(interval)
    }, [])

    // Auto-search when filters change
    useEffect(() => {
        const hasFilters = searchQuery.trim() || sender || dateRange.from || dateRange.to || minConfidence[0] > 0
        
        if (!hasFilters) {
            setSearchResults(null)
            return
        }

        const timer = setTimeout(() => {
            handleSearch()
        }, 500) // Debounce search by 500ms

        return () => clearTimeout(timer)
    }, [searchQuery, sender, dateRange.from, dateRange.to, minConfidence])

    const getCategoryColor = (category) => {
        const colors = {
            // Legacy categories
            spam: "bg-red-100 text-red-800",
            important: "bg-orange-100 text-orange-800",
            promotion: "bg-blue-100 text-blue-800",
            social: "bg-green-100 text-green-800",
            updates: "bg-purple-100 text-purple-800",
            // Enterprise departments
            sales: "bg-emerald-100 text-emerald-800",
            hr: "bg-pink-100 text-pink-800",
            finance: "bg-amber-100 text-amber-800",
            it_support: "bg-cyan-100 text-cyan-800",
            legal: "bg-slate-100 text-slate-800",
            marketing: "bg-violet-100 text-violet-800",
            customer_service: "bg-indigo-100 text-indigo-800",
            operations: "bg-teal-100 text-teal-800",
            executive: "bg-rose-100 text-rose-800",
            general: "bg-gray-100 text-gray-700",
            // Status
            pending: "bg-yellow-100 text-yellow-800",
            unclassified: "bg-gray-100 text-gray-500"
        }
        return colors[category?.toLowerCase()] || "bg-gray-100 text-gray-800"
    }

    const filteredEmails = selectedCategory === 'all' 
        ? allClassifications 
        : allClassifications.filter(email => email.category === selectedCategory)

    return (
        <div className="flex-1 flex flex-col h-screen bg-background">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <h2 className="text-3xl font-bold tracking-tight">
                            {searchResults !== null ? 'Search Results' : 'All Emails'}
                        </h2>
                        <div className="flex gap-2">
                            {searchResults !== null && (
                                <Button variant="outline" size="sm" onClick={clearSearch}>
                                    <X className="h-4 w-4 mr-2" />
                                    Clear Search
                                </Button>
                            )}
                            <Button onClick={fetchData} disabled={loading} size="sm">
                                <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
                                Refresh
                            </Button>
                        </div>
                    </div>

                    {/* Search & Filters Card */}
                    <Card className="border-blue-100">
                        <CardContent className="pt-6">
                            <form onSubmit={handleSearch} className="space-y-4">
                                <div className="flex gap-3">
                                    <div className="relative flex-1">
                                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            placeholder="Search by subject, body, or category..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-9 h-10"
                                        />
                                    </div>
                                    <Button
                                        type="button"
                                        variant={showFilters ? "secondary" : "outline"}
                                        onClick={() => setShowFilters(!showFilters)}
                                        className="h-10"
                                    >
                                        <Filter className="h-4 w-4 mr-2" />
                                        Filters
                                        {(sender || dateRange.from || dateRange.to || minConfidence[0] > 0) && (
                                            <span className="ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-xs font-bold text-white">
                                                {[sender, dateRange.from, dateRange.to, minConfidence[0] > 0].filter(Boolean).length}
                                            </span>
                                        )}
                                    </Button>
                                    <Button type="submit" disabled={isSearching} className="h-10">
                                        {isSearching && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        Search
                                    </Button>
                                </div>
                            </form>

                            {showFilters && (
                                <div className="mt-4 pt-4 border-t space-y-4 animate-in fade-in slide-in-from-top-2">
                                    <div className="grid gap-4 md:grid-cols-4">
                                        <div className="space-y-2">
                                            <Label className="text-xs font-semibold uppercase text-muted-foreground">Sender Email</Label>
                                            <Input
                                                placeholder="e.g., user@gmail.com"
                                                value={sender}
                                                onChange={(e) => setSender(e.target.value)}
                                                className="h-9"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <Label className="text-xs font-semibold uppercase text-muted-foreground">From Date</Label>
                                            <Popover>
                                                <PopoverTrigger asChild>
                                                    <Button
                                                        variant={"outline"}
                                                        className={cn(
                                                            "w-full justify-start text-left font-normal h-9",
                                                            !dateRange.from && "text-muted-foreground"
                                                        )}
                                                    >
                                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                                        {dateRange.from ? format(dateRange.from, "MMM d, yyyy") : <span>Select date</span>}
                                                    </Button>
                                                </PopoverTrigger>
                                                <PopoverContent className="w-auto p-0" align="start">
                                                    <Calendar
                                                        mode="single"
                                                        selected={dateRange.from}
                                                        onSelect={(date) => setDateRange(prev => ({ ...prev, from: date }))}
                                                    />
                                                </PopoverContent>
                                            </Popover>
                                        </div>

                                        <div className="space-y-2">
                                            <Label className="text-xs font-semibold uppercase text-muted-foreground">To Date</Label>
                                            <Popover>
                                                <PopoverTrigger asChild>
                                                    <Button
                                                        variant={"outline"}
                                                        className={cn(
                                                            "w-full justify-start text-left font-normal h-9",
                                                            !dateRange.to && "text-muted-foreground"
                                                        )}
                                                    >
                                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                                        {dateRange.to ? format(dateRange.to, "MMM d, yyyy") : <span>Select date</span>}
                                                    </Button>
                                                </PopoverTrigger>
                                                <PopoverContent className="w-auto p-0" align="start">
                                                    <Calendar
                                                        mode="single"
                                                        selected={dateRange.to}
                                                        onSelect={(date) => setDateRange(prev => ({ ...prev, to: date }))}
                                                    />
                                                </PopoverContent>
                                            </Popover>
                                        </div>

                                        <div className="space-y-2">
                                            <div className="flex justify-between items-center">
                                                <Label className="text-xs font-semibold uppercase text-muted-foreground">Min Confidence</Label>
                                                <span className="inline-flex items-center gap-1">
                                                    <span className="text-sm font-bold text-blue-600">{minConfidence[0]}</span>
                                                    <span className="text-xs text-muted-foreground">%</span>
                                                </span>
                                            </div>
                                            <Slider
                                                defaultValue={[0]}
                                                max={100}
                                                step={1}
                                                value={minConfidence}
                                                onValueChange={setMinConfidence}
                                                className="w-full"
                                            />
                                        </div>
                                    </div>

                                    {(sender || dateRange.from || dateRange.to || minConfidence[0] > 0) && (
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={clearSearch}
                                            className="text-xs"
                                        >
                                            <X className="h-3 w-3 mr-1" />
                                            Clear Filters
                                        </Button>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Category Filter Tabs */}
                    {searchResults === null && (
                        <div className="flex gap-2 overflow-x-auto pb-2">
                            <Button
                                variant={selectedCategory === 'all' ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setSelectedCategory('all')}
                            >
                                All ({allClassifications.length})
                            </Button>
                            {Object.entries(stats.category_breakdown || {}).map(([cat, count]) => (
                                <Button
                                    key={cat}
                                    variant={selectedCategory === cat ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setSelectedCategory(cat)}
                                    className="capitalize"
                                >
                                    {cat} ({count})
                                </Button>
                            ))}
                        </div>
                    )}

                    {/* Email Grid */}
                    <div className="space-y-4">
                        {searchResults !== null && (
                            <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <div>
                                    <p className="text-sm font-medium text-blue-900">
                                        Found <span className="font-bold text-blue-600">{searchResults.length}</span> matching emails
                                    </p>
                                    <p className="text-xs text-blue-700 mt-0.5">
                                        {searchQuery && `Search: "${searchQuery}"`}
                                        {sender && ` • From: ${sender}`}
                                        {minConfidence[0] > 0 && ` • Confidence: ≥${minConfidence[0]}%`}
                                    </p>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearSearch}
                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-100"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        )}

                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {loading && searchResults === null ? (
                                Array(6).fill(0).map((_, i) => (
                                    <div key={i} className="p-4 border rounded bg-card">
                                        <Skeleton className="h-4 w-3/4 mb-2" />
                                        <Skeleton className="h-3 w-1/2" />
                                    </div>
                                ))
                            ) : isSearching ? (
                                <div className="col-span-full flex items-center justify-center py-8">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                    <span className="ml-2 text-muted-foreground">Searching...</span>
                                </div>
                            ) : (searchResults !== null ? searchResults : filteredEmails).length === 0 ? (
                                <div className="col-span-full text-center py-12 text-muted-foreground">
                                    <p className="text-lg">No emails found</p>
                                    <p className="text-sm mt-1">Try adjusting your search or filters</p>
                                </div>
                            ) : (
                                (searchResults !== null ? searchResults : filteredEmails).map(email => (
                                <Card
                                    key={email.id}
                                    className="hover:shadow-md transition-all cursor-pointer"
                                    onClick={() => {
                                        setSelectedEmail(email)
                                        setDetailModalOpen(true)
                                    }}
                                >
                                    <CardContent className="p-4">
                                        <h3 className="font-semibold text-sm line-clamp-2 mb-2">
                                            {email.subject || email.email_subject || '(No Subject)'}
                                        </h3>
                                        <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                                            {email.body || email.email_body || 'No body content'}
                                        </p>
                                        <div className="flex flex-wrap gap-2 mb-3">
                                            {email.category && (
                                                <span className={cn("text-xs px-2 py-1 rounded font-bold", getCategoryColor(email.category))}>
                                                    {email.category}
                                                </span>
                                            )}
                                            {email.confidence && (
                                                <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                                                    {(email.confidence > 1 ? email.confidence : email.confidence * 100).toFixed(0)}%
                                                </span>
                                            )}

                                            {/* Entity Badges */}
                                            {email.entities?.dates?.map((date, i) => (
                                                <span key={`date-${i}`} className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                                                    📅 {date}
                                                </span>
                                            ))}
                                            {email.entities?.amounts?.map((amount, i) => (
                                                <span key={`amt-${i}`} className="text-xs px-2 py-1 rounded bg-green-100 text-green-800">
                                                    💰 {amount}
                                                </span>
                                            ))}
                                        </div>

                                        <p className="text-xs text-muted-foreground mb-3 line-clamp-1">
                                            From: {email.sender || email.email_sender || 'Unknown'}
                                        </p>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="w-full"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                handleGenerateReply(email)
                                            }}
                                            disabled={generatingReply === email.id}
                                        >
                                            {generatingReply === email.id ? (
                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                            ) : (
                                                <Sparkles className="mr-2 h-3 w-3 text-yellow-500" />
                                            )}
                                            Generate Reply
                                        </Button>
                                    </CardContent>
                                </Card>
                            ))
                        )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Smart Reply Dialog */}
            <Dialog open={!!replyDraft} onOpenChange={(open) => !open && setReplyDraft(null)}>
                <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-yellow-500" />
                            Smart Reply Draft
                        </DialogTitle>
                        <DialogDescription>
                            AI-generated reply based on analysis
                        </DialogDescription>
                    </DialogHeader>
                    {replyDraft && (
                        <div className="space-y-4 py-4">
                            {/* Analysis Summary */}
                            {replyDraft.analysis && (
                                <div className="flex flex-wrap gap-2 p-3 bg-purple-50 rounded-lg">
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
                                    {replyDraft.analysis.entities_found > 0 && (
                                        <span className="text-xs px-2 py-1 rounded bg-purple-100 text-purple-800 font-medium">
                                            🔍 {replyDraft.analysis.entities_found} entities
                                        </span>
                                    )}
                                </div>
                            )}
                            <div className="space-y-2">
                                <Label>Subject</Label>
                                <Input value={replyDraft.subject} readOnly />
                            </div>
                            <div className="space-y-2">
                                <Label>Body</Label>
                                <Textarea value={replyDraft.body} readOnly className="h-[200px]" />
                            </div>
                        </div>
                    )}
                    <DialogFooter className="sm:justify-between">
                        <Button variant="ghost" onClick={() => setReplyDraft(null)}>Close</Button>
                        <Button onClick={copyToClipboard} className="gap-2">
                            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            {copied ? "Copied" : "Copy to Clipboard"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Email Detail Modal */}
            <Suspense fallback={null}>
                <EmailDetailModal
                    isOpen={detailModalOpen}
                    onClose={() => {
                        setDetailModalOpen(false)
                        setSelectedEmail(null)
                    }}
                    emailId={selectedEmail?.id}
                    emailData={selectedEmail}
                />
            </Suspense>
        </div>
    )
}

export default EmailsPage
