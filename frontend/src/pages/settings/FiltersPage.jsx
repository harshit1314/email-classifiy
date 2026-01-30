import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Loader2, Plus, Trash2, Shield, AlertCircle } from 'lucide-react'

const FiltersPage = () => {
    const { API_URL } = useAuth()
    const [filters, setFilters] = useState({ ignored_senders: [], ignored_subjects: [] })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [newSender, setNewSender] = useState('')
    const [newKeyword, setNewKeyword] = useState('')
    const [actionLoading, setActionLoading] = useState(false)

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

    const fetchFilters = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/filters`)
            setFilters(response.data)
            setError(null)
        } catch (err) {
            console.error('Failed to fetch filters:', err)
            setError('Failed to load filters. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchFilters()
    }, [])

    const handleAddSender = async (e) => {
        e.preventDefault()
        if (!newSender.trim()) return

        setActionLoading(true)
        try {
            await axios.post(`${API_URL}/api/filters/sender`, { sender: newSender.trim() })
            setNewSender('')
            await fetchFilters()
        } catch (err) {
            setError('Failed to add sender: ' + formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message))
        } finally {
            setActionLoading(false)
        }
    }

    const handleRemoveSender = async (sender) => {
        if (!confirm(`Unblock sender "${sender}"?`)) return

        setActionLoading(true)
        try {
            // Check for DELETE body issue - Axios delete with body needs specific syntax
            await axios.delete(`${API_URL}/api/filters/sender`, { data: { sender } })
            await fetchFilters()
        } catch (err) {
            setError('Failed to remove sender: ' + formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message))
        } finally {
            setActionLoading(false)
        }
    }

    const handleAddKeyword = async (e) => {
        e.preventDefault()
        if (!newKeyword.trim()) return

        setActionLoading(true)
        try {
            await axios.post(`${API_URL}/api/filters/subject`, { keyword: newKeyword.trim() })
            setNewKeyword('')
            await fetchFilters()
        } catch (err) {
            setError('Failed to add keyword: ' + formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message))
        } finally {
            setActionLoading(false)
        }
    }

    const handleRemoveKeyword = async (keyword) => {
        if (!confirm(`Unblock keyword "${keyword}"?`)) return

        setActionLoading(true)
        try {
            await axios.delete(`${API_URL}/api/filters/subject`, { data: { keyword } })
            await fetchFilters()
        } catch (err) {
            setError('Failed to remove keyword: ' + formatErrorMessage(err.response?.data?.detail || err.response?.data || err.message))
        } finally {
            setActionLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Live Filters</h2>
                <p className="text-muted-foreground">Manage blocked senders and unwanted subjects</p>
            </div>

            {error && (
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6 text-red-600 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        {error}
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                {/* Blocked Senders */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-red-500" />
                            Blocked Senders
                        </CardTitle>
                        <CardDescription>Emails from these addresses will be skipped</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <form onSubmit={handleAddSender} className="flex gap-2">
                            <Input
                                placeholder="example: spammer@domain.com"
                                value={newSender}
                                onChange={(e) => setNewSender(e.target.value)}
                                disabled={actionLoading}
                            />
                            <Button type="submit" disabled={!newSender.trim() || actionLoading}>
                                <Plus className="h-4 w-4" />
                            </Button>
                        </form>

                        <div className="space-y-2 mt-4 max-h-[300px] overflow-y-auto">
                            {filters.ignored_senders.length === 0 ? (
                                <p className="text-sm text-muted-foreground text-center py-4">No blocked senders</p>
                            ) : (
                                filters.ignored_senders.map((sender) => (
                                    <div key={sender} className="flex items-center justify-between p-2 rounded-md border bg-muted/20">
                                        <span className="text-sm font-medium">{sender}</span>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => handleRemoveSender(sender)}
                                            disabled={actionLoading}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Blocked Subjects */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-orange-500" />
                            Blocked Keywords
                        </CardTitle>
                        <CardDescription>Emails with these words in the subject will be skipped</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <form onSubmit={handleAddKeyword} className="flex gap-2">
                            <Input
                                placeholder="example: lottery, prize"
                                value={newKeyword}
                                onChange={(e) => setNewKeyword(e.target.value)}
                                disabled={actionLoading}
                            />
                            <Button type="submit" disabled={!newKeyword.trim() || actionLoading}>
                                <Plus className="h-4 w-4" />
                            </Button>
                        </form>

                        <div className="space-y-2 mt-4 max-h-[300px] overflow-y-auto">
                            {filters.ignored_subjects.length === 0 ? (
                                <p className="text-sm text-muted-foreground text-center py-4">No blocked keywords</p>
                            ) : (
                                filters.ignored_subjects.map((keyword) => (
                                    <div key={keyword} className="flex items-center justify-between p-2 rounded-md border bg-muted/20">
                                        <span className="text-sm font-medium">{keyword}</span>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => handleRemoveKeyword(keyword)}
                                            disabled={actionLoading}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default FiltersPage
