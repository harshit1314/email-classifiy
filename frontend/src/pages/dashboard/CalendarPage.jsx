import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Loader2, CalendarDays, Plus, Sparkles, Clock, MapPin, Users, Mail, Zap, CheckCircle2, Video } from 'lucide-react'
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
            const response = await axios.get(`${API_URL}/api/calendar/events?limit=10`, {
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
                setEvents(prev => [...prev, ...response.data.meetings])
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

    const upcomingEvents = events
        .filter(event => {
            const eventDate = new Date(event.start_time || event.start || event.date)
            return eventDate >= new Date()
        })
        .sort((a, b) => {
            const dateA = new Date(a.start_time || a.start || a.date)
            const dateB = new Date(b.start_time || b.start || b.date)
            return dateA - dateB
        })
        .slice(0, 5)

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

                    <div className="grid gap-6 md:grid-cols-3">
                        {/* Calendar Widget */}
                        <div className="md:col-span-2">
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
                        </div>

                        {/* Upcoming Events Sidebar */}
                        <div>
                            <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-cyan-600 text-white h-full">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-xl text-white">
                                        <Clock className="h-5 w-5" />
                                        Upcoming Events
                                    </CardTitle>
                                    <CardDescription className="text-blue-100">Next 5 scheduled events</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {upcomingEvents.length > 0 ? (
                                        <div className="space-y-3">
                                            {upcomingEvents.map((event, idx) => (
                                                <div
                                                    key={idx}
                                                    className="group rounded-lg bg-white/20 backdrop-blur border border-white/30 p-4 hover:bg-white/30 transition-all duration-200"
                                                >
                                                    <div className="flex items-start justify-between mb-2">
                                                        <h4 
                                                            className="font-semibold text-white flex items-center gap-2 cursor-pointer flex-1"
                                                            onClick={() => setSelectedEvent(event)}
                                                        >
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
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-6 w-6 p-0 text-red-200 hover:text-red-100 hover:bg-red-500/20"
                                                                onClick={(e) => {
                                                                    e.stopPropagation()
                                                                    if (window.confirm('Delete this meeting?')) {
                                                                        handleDeleteEvent(event.id)
                                                                    }
                                                                }}
                                                            >
                                                                ✕
                                                            </Button>
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
                                            <p className="text-xs text-blue-200 mt-1">Extract meetings from emails below</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </div>

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
            </div>
        </div>
    )
}

export default CalendarPage
