import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Loader2, CalendarDays, Plus, Sparkles, Clock, MapPin, Users, Mail, Zap, CheckCircle2, Video, X, Search, Filter, TrendingUp, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from "@/components/ui/use-toast"

const CalendarPage = () => {
    const { API_URL, token } = useAuth()
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

    const [date, setDate] = useState(new Date())
    const [events, setEvents] = useState([])
    const [emailText, setEmailText] = useState('')
    const [extracting, setExtracting] = useState(false)
    const [autoExtracting, setAutoExtracting] = useState(false)
    const [selectedEvent, setSelectedEvent] = useState(null)
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterType, setFilterType] = useState('all') // all, virtual, in-person
    const [copiedLink, setCopiedLink] = useState(false)

    useEffect(() => {
        let mounted = true
        const loadEvents = async () => {
            if (mounted) await fetchEvents()
        }
        loadEvents()
        return () => { mounted = false }
    }, [])

    const fetchEvents = async () => {
        try {
            setLoading(true)
            const response = await axios.get(`${API_URL}/api/calendar/events?limit=100`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setEvents(response.data.events || [])
        } catch (err) {
            console.error('Failed to fetch events:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleAutoExtract = async () => {
        setAutoExtracting(true)
        try {
            const response = await axios.post(
                `${API_URL}/api/calendar/extract-from-classified`,
                { limit: 50, days_back: 7 },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            const message = response.data.skipped_duplicates > 0
                ? `Found ${response.data.total_extracted} meeting(s) from ${response.data.emails_processed} emails (${response.data.skipped_duplicates} duplicates skipped)`
                : `Found ${response.data.total_extracted} meeting(s) from ${response.data.emails_processed} emails`;

            toast({
                title: "Auto-Extraction Complete",
                description: message,
            })

            if (response.data.meetings && response.data.meetings.length > 0) {
                await fetchEvents()  // Refresh events
            }
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Auto-Extraction Failed",
                description: formatErrorMessage(err.response?.data?.detail || err.message)
            })
        } finally {
            setAutoExtracting(false)
        }
    }

    const handleDeleteEvent = async (eventId) => {
        try {
            await axios.delete(`${API_URL}/api/calendar/events/${eventId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })

            toast({
                title: "Event Deleted",
                description: "Meeting removed from calendar",
            })

            setSelectedEvent(null)
            await fetchEvents()  // Refresh events
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Delete Failed",
                description: formatErrorMessage(err.response?.data?.detail || err.message)
            })
        }
    }

    const handleExtractMeeting = async () => {
        if (!emailText.trim()) {
            toast({
                variant: "destructive",
                title: "No Content",
                description: "Please paste email content first"
            })
            return
        }

        setExtracting(true)
        try {
            const response = await axios.post(
                `${API_URL}/api/calendar/extract-meeting`,
                { email_text: emailText },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            toast({
                title: "Meeting Extracted",
                description: `Found ${response.data.meetings?.length || 0} meeting(s)`,
            })

            if (response.data.meetings && response.data.meetings.length > 0) {
                setEmailText('')
                await fetchEvents()  // Refresh to get saved events
            }
        } catch (err) {
            toast({
                variant: "destructive",
                title: "Extraction Failed",
                description: formatErrorMessage(err.response?.data?.detail || err.response?.data?.message || err.message)
            })
        } finally {
            setExtracting(false)
        }
    }

    const copyMeetingLink = (link) => {
        navigator.clipboard.writeText(link)
        setCopiedLink(true)
        toast({
            title: "Link Copied",
            description: "Meeting link copied to clipboard",
        })
        setTimeout(() => setCopiedLink(false), 2000)
    }

    // Filter and search events
    const filteredEvents = events.filter(event => {
        const matchesSearch = !searchQuery ||
            (event.event_title || event.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
            (event.location || '').toLowerCase().includes(searchQuery.toLowerCase())

        const matchesFilter = filterType === 'all' ||
            (filterType === 'virtual' && event.meeting_link) ||
            (filterType === 'in-person' && !event.meeting_link && event.location)

        return matchesSearch && matchesFilter
    })

    const upcomingEvents = filteredEvents
        .filter(event => {
            const eventDate = new Date(event.start_time || event.start || event.date)
            return eventDate >= new Date()
        })
        .sort((a, b) => {
            const dateA = new Date(a.start_time || a.start || a.date)
            const dateB = new Date(b.start_time || b.start || b.date)
            return dateA - dateB
        })

    const pastEvents = filteredEvents
        .filter(event => {
            const eventDate = new Date(event.start_time || event.start || event.date)
            return eventDate < new Date()
        })
        .sort((a, b) => {
            const dateA = new Date(a.start_time || a.start || a.date)
            const dateB = new Date(b.start_time || b.start || b.date)
            return dateB - dateA
        })

    // Statistics
    const totalEvents = events.length
    const virtualMeetings = events.filter(e => e.meeting_link).length
    const inPersonMeetings = events.filter(e => !e.meeting_link && e.location).length

    const getEventColor = (event) => {
        if (event.meeting_link) return 'from-blue-500 to-cyan-600'
        if (event.location) return 'from-purple-500 to-pink-600'
        return 'from-gray-500 to-gray-600'
    }

    return (
        <div className="flex-1 flex flex-col h-screen bg-transparent">
            <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-2">
                                Calendar
                            </h2>
                            <p className="text-sm text-muted-foreground">Manage your schedule and extract meetings from emails</p>
                        </div>
                        <Button
                            onClick={handleAutoExtract}
                            disabled={autoExtracting}
                            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                        >
                            {autoExtracting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Scanning Emails...
                                </>
                            ) : (
                                <>
                                    <Zap className="mr-2 h-4 w-4" />
                                    Auto-Extract from Emails
                                </>
                            )}
                        </Button>
                    </div>

                    {/* Statistics Cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-cyan-600 text-white">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-blue-100">Total Events</p>
                                        <p className="text-3xl font-bold">{totalEvents}</p>
                                    </div>
                                    <CalendarDays className="h-12 w-12 text-white/50" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-pink-600 text-white">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-purple-100">Virtual Meetings</p>
                                        <p className="text-3xl font-bold">{virtualMeetings}</p>
                                    </div>
                                    <Video className="h-12 w-12 text-white/50" />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-500 to-red-600 text-white">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-orange-100">In-Person</p>
                                        <p className="text-3xl font-bold">{inPersonMeetings}</p>
                                    </div>
                                    <MapPin className="h-12 w-12 text-white/50" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-6 md:grid-cols-3">
                        {/* Calendar Widget */}
                        <div className="md:col-span-2 space-y-6">
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 p-2">
                                            <CalendarDays className="h-5 w-5 text-white" />
                                        </div>
                                        Your Calendar
                                    </CardTitle>
                                    <CardDescription>Select a date to view or add events</CardDescription>
                                </CardHeader>
                                <CardContent className="flex justify-center">
                                    <div className="rounded-xl border-2 border-gray-100 p-4 bg-gradient-to-br from-blue-50/50 to-cyan-50/50">
                                        <Calendar
                                            mode="single"
                                            selected={date}
                                            onSelect={setDate}
                                            className="rounded-lg"
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            {/* AI Meeting Extraction */}
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-2xl">
                                        <div className="rounded-full bg-gradient-to-br from-purple-500 to-pink-600 p-2">
                                            <Sparkles className="h-5 w-5 text-white" />
                                        </div>
                                        AI Meeting Extraction
                                    </CardTitle>
                                    <CardDescription>Paste email content to automatically extract meeting details</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-sm font-semibold">Email Content</label>
                                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                    <Mail className="h-3 w-3" />
                                                    <span>Powered by AI</span>
                                                </div>
                                            </div>
                                            <Textarea
                                                placeholder="Paste email text here... AI will extract meeting details like date, time, location, and attendees."
                                                value={emailText}
                                                onChange={e => setEmailText(e.target.value)}
                                                rows={8}
                                                className="resize-none font-mono text-sm"
                                            />
                                        </div>

                                        <div className="rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 p-4">
                                            <p className="text-sm text-purple-900">
                                                <strong>Tip:</strong> The AI can extract meeting information including date, time, location, attendees, and agenda from natural language text.
                                            </p>
                                        </div>

                                        <Button
                                            onClick={handleExtractMeeting}
                                            disabled={extracting || !emailText.trim()}
                                            className="w-full h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-lg"
                                        >
                                            {extracting ? (
                                                <>
                                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                                    Extracting Meeting Details...
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles className="mr-2 h-5 w-5" />
                                                    Extract Meeting
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Events List Sidebar */}
                        <div className="space-y-4">
                            {/* Search and Filter */}
                            <Card className="border-0 shadow-lg bg-white/90 backdrop-blur">
                                <CardContent className="p-4 space-y-3">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <Input
                                            placeholder="Search events..."
                                            value={searchQuery}
                                            onChange={e => setSearchQuery(e.target.value)}
                                            className="pl-10"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            size="sm"
                                            variant={filterType === 'all' ? 'default' : 'outline'}
                                            onClick={() => setFilterType('all')}
                                            className="flex-1"
                                        >
                                            All
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant={filterType === 'virtual' ? 'default' : 'outline'}
                                            onClick={() => setFilterType('virtual')}
                                            className="flex-1"
                                        >
                                            <Video className="h-3 w-3 mr-1" />
                                            Virtual
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant={filterType === 'in-person' ? 'default' : 'outline'}
                                            onClick={() => setFilterType('in-person')}
                                            className="flex-1"
                                        >
                                            <MapPin className="h-3 w-3 mr-1" />
                                            In-Person
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Upcoming Events */}
                            <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-cyan-600 text-white">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-xl text-white">
                                        <Clock className="h-5 w-5" />
                                        Upcoming Events
                                    </CardTitle>
                                    <CardDescription className="text-blue-100">Next scheduled events</CardDescription>
                                </CardHeader>
                                <CardContent className="max-h-[600px] overflow-y-auto">
                                    {upcomingEvents.length > 0 ? (
                                        <div className="space-y-3">
                                            {upcomingEvents.slice(0, 10).map((event, idx) => (
                                                <div
                                                    key={idx}
                                                    className="group rounded-lg bg-white/20 backdrop-blur border border-white/30 p-4 hover:bg-white/30 transition-all duration-200 cursor-pointer"
                                                    onClick={() => setSelectedEvent(event)}
                                                >
                                                    <div className="flex items-start justify-between mb-2">
                                                        <h4 className="font-semibold text-white flex items-center gap-2 flex-1">
                                                            <div className="w-2 h-2 rounded-full bg-yellow-300 animate-pulse"></div>
                                                            {event.event_title || event.title || event.summary || 'Untitled Event'}
                                                        </h4>
                                                        <div className="flex items-center gap-2">
                                                            {(event.confidence === 'high' || event.has_date && event.has_time) && (
                                                                <Badge className="bg-green-500/20 text-green-100 border-green-300">
                                                                    <CheckCircle2 className="h-3 w-3 mr-1" />
                                                                    High
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="space-y-1 text-sm text-blue-50">
                                                        <p className="flex items-center gap-2">
                                                            <Clock className="h-3 w-3" />
                                                            {new Date(event.start_time || event.start || event.date).toLocaleString()}
                                                        </p>
                                                        {event.location && (
                                                            <p className="flex items-center gap-2">
                                                                {event.meeting_link ? <Video className="h-3 w-3" /> : <MapPin className="h-3 w-3" />}
                                                                {event.location}
                                                            </p>
                                                        )}
                                                        {event.attendees && event.attendees.length > 0 && (
                                                            <p className="flex items-center gap-2">
                                                                <Users className="h-3 w-3" />
                                                                {event.attendees.length} attendee(s)
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-12">
                                            <CalendarDays className="h-12 w-12 mx-auto mb-3 text-white/50" />
                                            <p className="text-blue-100">No upcoming events</p>
                                            <p className="text-xs text-blue-200 mt-1">Extract meetings from emails to get started</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </div>
            </div>

            {/* Event Detail Modal */}
            <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="text-2xl flex items-center gap-2">
                            <div className={`rounded-full bg-gradient-to-br ${getEventColor(selectedEvent || {})} p-2`}>
                                {selectedEvent?.meeting_link ? <Video className="h-5 w-5 text-white" /> : <CalendarDays className="h-5 w-5 text-white" />}
                            </div>
                            {selectedEvent?.event_title || selectedEvent?.title || selectedEvent?.summary || 'Event Details'}
                        </DialogTitle>
                        <DialogDescription>
                            {selectedEvent?.has_date && selectedEvent?.has_time ? 'Confirmed meeting details' : 'Meeting information'}
                        </DialogDescription>
                    </DialogHeader>

                    {selectedEvent && (
                        <div className="space-y-4 mt-4">
                            {/* Date & Time */}
                            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
                                <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
                                <div>
                                    <p className="font-semibold text-blue-900">Date & Time</p>
                                    <p className="text-sm text-blue-700">
                                        {new Date(selectedEvent.start_time || selectedEvent.start || selectedEvent.date).toLocaleString()}
                                    </p>
                                    {selectedEvent.end_time && (
                                        <p className="text-xs text-blue-600 mt-1">
                                            Ends: {new Date(selectedEvent.end_time).toLocaleString()}
                                        </p>
                                    )}
                                </div>
                            </div>

                            {/* Location */}
                            {selectedEvent.location && (
                                <div className="flex items-start gap-3 p-4 bg-purple-50 rounded-lg border border-purple-100">
                                    {selectedEvent.meeting_link ? <Video className="h-5 w-5 text-purple-600 mt-0.5" /> : <MapPin className="h-5 w-5 text-purple-600 mt-0.5" />}
                                    <div className="flex-1">
                                        <p className="font-semibold text-purple-900">Location</p>
                                        <p className="text-sm text-purple-700">{selectedEvent.location}</p>
                                        {selectedEvent.meeting_link && (
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                className="mt-2"
                                                onClick={() => copyMeetingLink(selectedEvent.meeting_link)}
                                            >
                                                {copiedLink ? <Check className="h-3 w-3 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                                                {copiedLink ? 'Copied!' : 'Copy Link'}
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Attendees */}
                            {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
                                <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-100">
                                    <Users className="h-5 w-5 text-green-600 mt-0.5" />
                                    <div>
                                        <p className="font-semibold text-green-900">Attendees ({selectedEvent.attendees.length})</p>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {selectedEvent.attendees.map((attendee, i) => (
                                                <Badge key={i} variant="outline" className="bg-white">
                                                    {attendee}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Description */}
                            {selectedEvent.event_description && (
                                <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                    <p className="font-semibold text-gray-900 mb-2">Description</p>
                                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedEvent.event_description}</p>
                                </div>
                            )}

                            {/* Confidence Badge */}
                            {selectedEvent.confidence && (
                                <div className="flex items-center gap-2">
                                    <Badge className={selectedEvent.confidence === 'high' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                                        {selectedEvent.confidence === 'high' ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <TrendingUp className="h-3 w-3 mr-1" />}
                                        {selectedEvent.confidence.charAt(0).toUpperCase() + selectedEvent.confidence.slice(1)} Confidence
                                    </Badge>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2 pt-4 border-t">
                                <Button
                                    variant="destructive"
                                    onClick={() => {
                                        if (window.confirm('Delete this meeting?')) {
                                            handleDeleteEvent(selectedEvent.id)
                                        }
                                    }}
                                    className="flex-1"
                                >
                                    <X className="h-4 w-4 mr-2" />
                                    Delete Event
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setSelectedEvent(null)}
                                    className="flex-1"
                                >
                                    Close
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    )
}

export default CalendarPage

