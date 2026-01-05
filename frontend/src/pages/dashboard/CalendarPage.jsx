import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Calendar } from '@/components/ui/calendar'
import { Loader2, Calendar as CalendarIcon, MapPin, Clock, Plus, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'

const CalendarPage = () => {
    const { API_URL, token } = useAuth()
    const [events, setEvents] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedDate, setSelectedDate] = useState(new Date())
    const [currentMonth, setCurrentMonth] = useState(new Date())

    // Extraction State
    const [extractText, setExtractText] = useState('')
    const [extracting, setExtracting] = useState(false)

    const fetchEvents = async () => {
        setLoading(true)
        try {
            const response = await axios.get(`${API_URL}/api/calendar/events`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setEvents(response.data.events || [])
        } catch (err) {
            console.error('Failed to fetch events:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchEvents()
    }, [])

    // Get events for selected date
    const getEventsForDate = (date) => {
        if (!date) return []
        return events.filter(event => {
            const eventDate = new Date(event.start_time)
            return eventDate.toDateString() === date.toDateString()
        })
    }

    // Check if a date has events
    const hasEvents = (date) => {
        return events.some(event => {
            const eventDate = new Date(event.start_time)
            return eventDate.toDateString() === date.toDateString()
        })
    }

    const selectedDateEvents = getEventsForDate(selectedDate)

    const handleExtract = async (e) => {
        e.preventDefault()
        if (!extractText.trim()) return

        setExtracting(true)
        try {
            const response = await axios.post(`${API_URL}/api/calendar/extract-meeting`, {
                email_body: extractText,
                email_subject: "Manual Extraction"
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            if (response.data.meeting_found) {
                alert('Meeting found and added to calendar!')
                setExtractText('')
                fetchEvents()
            } else {
                alert('No meeting details found in the text.')
            }
        } catch (err) {
            alert('Failed to extract meeting: ' + (err.response?.data?.detail || err.message))
        } finally {
            setExtracting(false)
        }
    }

    // Navigation handlers
    const goToPreviousMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
    }

    const goToNextMonth = () => {
        setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
    }

    const goToToday = () => {
        const today = new Date()
        setCurrentMonth(today)
        setSelectedDate(today)
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Calendar</h2>
                <Button variant="outline" onClick={fetchEvents}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                {/* Calendar Widget */}
                <div className="lg:col-span-2 space-y-4">
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg">
                                    {currentMonth.toLocaleString('default', { month: 'long', year: 'numeric' })}
                                </CardTitle>
                                <div className="flex items-center gap-2">
                                    <Button variant="outline" size="sm" onClick={goToToday}>
                                        Today
                                    </Button>
                                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={goToPreviousMonth}>
                                        <ChevronLeft className="h-4 w-4" />
                                    </Button>
                                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={goToNextMonth}>
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <Calendar
                                mode="single"
                                selected={selectedDate}
                                onSelect={setSelectedDate}
                                month={currentMonth}
                                onMonthChange={setCurrentMonth}
                                className="rounded-md border w-full"
                                classNames={{
                                    month: "space-y-4 w-full",
                                    month_caption: "hidden",
                                    month_grid: "w-full border-collapse",
                                    weekdays: "flex w-full",
                                    weekday: "text-muted-foreground font-normal text-sm flex-1 text-center py-2",
                                    week: "flex w-full",
                                    day: "flex-1 text-center p-0 relative",
                                    day_button: "w-full h-12 p-0 font-normal hover:bg-accent rounded-md",
                                    selected: "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground",
                                    today: "bg-accent text-accent-foreground font-bold",
                                    outside: "text-muted-foreground opacity-50",
                                }}
                                modifiers={{
                                    hasEvent: (date) => hasEvents(date)
                                }}
                                modifiersClassNames={{
                                    hasEvent: "after:absolute after:bottom-1 after:left-1/2 after:-translate-x-1/2 after:w-1.5 after:h-1.5 after:bg-blue-500 after:rounded-full"
                                }}
                            />
                        </CardContent>
                    </Card>

                    {/* Selected Date Events */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <CalendarIcon className="h-5 w-5" />
                                {selectedDate ? selectedDate.toLocaleDateString('default', { 
                                    weekday: 'long', 
                                    month: 'long', 
                                    day: 'numeric',
                                    year: 'numeric'
                                }) : 'Select a date'}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center p-4">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : selectedDateEvents.length === 0 ? (
                                <p className="text-muted-foreground text-center py-4">
                                    No events scheduled for this day.
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {selectedDateEvents.map((event) => (
                                        <div key={event.id} className="flex gap-3 p-3 bg-accent/30 rounded-lg">
                                            <div className="flex flex-col items-center justify-center min-w-[50px] bg-primary/10 rounded-md p-2 text-primary">
                                                <Clock className="h-4 w-4 mb-1" />
                                                <span className="text-xs font-bold">
                                                    {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold">{event.summary}</h4>
                                                {event.location && (
                                                    <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                                                        <MapPin className="h-3 w-3" />
                                                        {event.location}
                                                    </p>
                                                )}
                                                {event.description && (
                                                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                        {event.description}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right Sidebar */}
                <div className="space-y-6">
                    {/* Upcoming Events Summary */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">Upcoming Events</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center p-4">
                                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                </div>
                            ) : events.length === 0 ? (
                                <p className="text-sm text-muted-foreground text-center py-2">
                                    No upcoming events.
                                </p>
                            ) : (
                                <div className="space-y-2">
                                    {events.slice(0, 5).map((event) => (
                                        <div 
                                            key={event.id} 
                                            className="p-2 rounded hover:bg-accent/50 cursor-pointer transition-colors"
                                            onClick={() => {
                                                const eventDate = new Date(event.start_time)
                                                setSelectedDate(eventDate)
                                                setCurrentMonth(eventDate)
                                            }}
                                        >
                                            <p className="font-medium text-sm truncate">{event.summary}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {new Date(event.start_time).toLocaleDateString('default', { 
                                                    month: 'short', 
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </p>
                                        </div>
                                    ))}
                                    {events.length > 5 && (
                                        <p className="text-xs text-muted-foreground text-center pt-2">
                                            +{events.length - 5} more events
                                        </p>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* AI Meeting Extraction */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">AI Meeting Extraction</CardTitle>
                            <CardDescription className="text-xs">Paste email content to automatically extract and schedule meetings.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleExtract} className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="text-sm">Email Content</Label>
                                    <Textarea
                                        placeholder="e.g. 'Lets meet tomorrow at 2pm for the project review'"
                                        className="min-h-[120px] text-sm"
                                        value={extractText}
                                        onChange={(e) => setExtractText(e.target.value)}
                                    />
                                </div>
                                <Button className="w-full" type="submit" disabled={extracting || !extractText.trim()}>
                                    {extracting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                                    Extract & Schedule
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}

export default CalendarPage
