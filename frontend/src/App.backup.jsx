import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'http://localhost:8002'

function App() {
  const [activeTab, setActiveTab] = useState('classify')
  const [email, setEmail] = useState({
    subject: '',
    body: '',
    sender: ''
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authMode, setAuthMode] = useState('login') // 'login' or 'register'
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ email: '', password: '', full_name: '' })
  
  // Dashboard state
  const [statistics, setStatistics] = useState(null)
  const [classifications, setClassifications] = useState([])
  const [actionRules, setActionRules] = useState({})
  const [monitoring, setMonitoring] = useState(null)
  const [refreshInterval, setRefreshInterval] = useState(null)
  
  // New features state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchCategory, setSearchCategory] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [customCategories, setCustomCategories] = useState([])
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [selectedClassification, setSelectedClassification] = useState(null)
  
  // Model Retraining state
  const [retrainingStatus, setRetrainingStatus] = useState(null)
  const [retrainingInProgress, setRetrainingInProgress] = useState(false)
  
  // Auto-Reply Templates state
  const [autoReplyTemplates, setAutoReplyTemplates] = useState([])
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [newTemplate, setNewTemplate] = useState({ name: '', subject: '', body: '', category_filter: '', sender_filter: '', keywords: [] })
  
  // Email Scheduling state
  const [scheduledEmails, setScheduledEmails] = useState([])
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [newScheduledEmail, setNewScheduledEmail] = useState({ recipient: '', subject: '', body: '', scheduled_time: '' })
  
  // Calendar state
  const [calendarEvents, setCalendarEvents] = useState([])
  
  // Reports state
  const [reportTemplates, setReportTemplates] = useState([])
  const [generatedReports, setGeneratedReports] = useState([])
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportFilters, setReportFilters] = useState({ category: '', start_date: '', end_date: '', min_confidence: 0.7 })
  
  // Tasks state
  const [tasks, setTasks] = useState([])
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [newTask, setNewTask] = useState({ email_subject: '', email_body: '', task_type: 'general', priority: 'medium', due_date: '' })
  
  // Email polling state
  const [emailPollingStatus, setEmailPollingStatus] = useState(null)
  const [gmailConnecting, setGmailConnecting] = useState(false)
  const [outlookConnecting, setOutlookConnecting] = useState(false)
  
  // Theme state
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true')
  
  // Email marking state (starred, archived, read status)
  const [emailMarkings, setEmailMarkings] = useState(() => {
    const saved = localStorage.getItem('emailMarkings')
    return saved ? JSON.parse(saved) : {}
  })
  
  // Manual credentials input
  const [gmailCredentials, setGmailCredentials] = useState({ 
    client_id: '', 
    client_secret: '', 
    interval: 30 
  })
  const [outlookCredentials, setOutlookCredentials] = useState({
    client_id: '',
    client_secret: '',
    tenant_id: 'common',
    interval: 30
  })

  // Department Routing state
  const [routingStatus, setRoutingStatus] = useState(null)
  const [departments, setDepartments] = useState([])
  const [departmentEmails, setDepartmentEmails] = useState({})
  const [selectedDepartment, setSelectedDepartment] = useState(null)
  const [departmentsSummary, setDepartmentsSummary] = useState(null)
  const [loadingRouting, setLoadingRouting] = useState(false)

  // Check authentication on mount
  useEffect(() => {
    if (token) {
      checkAuth()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark-mode')
    } else {
      document.documentElement.classList.remove('dark-mode')
    }
    localStorage.setItem('darkMode', darkMode.toString())
  }, [darkMode])

  // Save email markings to localStorage
  useEffect(() => {
    localStorage.setItem('emailMarkings', JSON.stringify(emailMarkings))
  }, [emailMarkings])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ctrl/Cmd + K - Search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        if (isAuthenticated) {
          setActiveTab('search')
        }
      }
      // Ctrl/Cmd + D - Toggle dark mode
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault()
        setDarkMode(!darkMode)
      }
      // Ctrl/Cmd + 1 - Classify
      if ((e.ctrlKey || e.metaKey) && e.key === '1') {
        e.preventDefault()
        setActiveTab('classify')
      }
      // Ctrl/Cmd + 2 - Dashboard
      if ((e.ctrlKey || e.metaKey) && e.key === '2') {
        e.preventDefault()
        setActiveTab('dashboard')
      }
      // Ctrl/Cmd + 3 - Connect
      if ((e.ctrlKey || e.metaKey) && e.key === '3') {
        e.preventDefault()
        setActiveTab('connect')
      }
      // Escape - Close modals
      if (e.key === 'Escape') {
        setShowAuthModal(false)
        setShowFeedbackModal(false)
        setShowTemplateModal(false)
        setShowScheduleModal(false)
        setShowReportModal(false)
        setShowTaskModal(false)
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [darkMode, isAuthenticated, activeTab])

  // Fetch dashboard data
  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchStatistics()
      fetchClassifications()
      fetchActionRules()
      fetchMonitoring()
      if (isAuthenticated) {
        fetchAnalytics()
        fetchCustomCategories()
        fetchRetrainingStatus()
        fetchAutoReplyTemplates()
        fetchScheduledEmails()
        fetchCalendarEvents()
        fetchReportTemplates()
        fetchGeneratedReports()
        fetchTasks()
      }
      
      // Auto-refresh every 5 seconds
      const interval = setInterval(() => {
        fetchStatistics()
        fetchClassifications()
        fetchMonitoring()
        fetchEmailPollingStatus()
        if (isAuthenticated) {
          fetchAnalytics()
          fetchRetrainingStatus()
        }
      }, 5000)
      
      // Initial fetch
      fetchEmailPollingStatus()
      setRefreshInterval(interval)
      
      return () => clearInterval(interval)
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        setRefreshInterval(null)
      }
    }
  }, [activeTab, isAuthenticated])

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/statistics`)
      setStatistics(response.data)
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
    }
  }

  const fetchClassifications = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/classifications?limit=20`)
      setClassifications(response.data.classifications || [])
    } catch (err) {
      console.error('Failed to fetch classifications:', err)
    }
  }

  const fetchActionRules = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/actions/rules`)
      setActionRules(response.data.rules || {})
    } catch (err) {
      console.error('Failed to fetch action rules:', err)
    }
  }

  const fetchMonitoring = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/monitor`)
      setMonitoring(response.data)
    } catch (err) {
      console.error('Failed to fetch monitoring data:', err)
    }
  }

  const fetchEmailPollingStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/email/status`)
      setEmailPollingStatus(response.data)
    } catch (err) {
      console.error('Failed to fetch email polling status:', err)
      setEmailPollingStatus(null)
    }
  }

  // Fetch status when on connect tab
  useEffect(() => {
    if (activeTab === 'connect') {
      fetchEmailPollingStatus()
      const interval = setInterval(() => {
        fetchEmailPollingStatus()
      }, 3000) // Check every 3 seconds when on connect page
      return () => clearInterval(interval)
    }
  }, [activeTab])

  const handleStartGmail = async () => {
    if (!gmailCredentials.client_id || !gmailCredentials.client_secret) {
      alert('Please enter both Client ID and Client Secret')
      return
    }
    
    setGmailConnecting(true)
    try {
      const response = await axios.post(`${API_URL}/api/email/start-gmail`, {
        client_id: gmailCredentials.client_id,
        client_secret: gmailCredentials.client_secret,
        interval: parseInt(gmailCredentials.interval) || 30
      })
      alert(response.data.message || 'Gmail polling started! Check your browser for OAuth authorization.')
      fetchEmailPollingStatus()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Unknown error'
      console.error('Gmail connection error:', err.response?.data || err)
      alert(`Failed to start Gmail polling:\n\n${errorMsg}\n\nCheck the backend console for more details.`)
    } finally {
      setGmailConnecting(false)
    }
  }

  const handleStartOutlook = async () => {
    if (!outlookCredentials.client_id) {
      alert('Please enter Client ID')
      return
    }
    
    setOutlookConnecting(true)
    try {
      const response = await axios.post(`${API_URL}/api/email/start-outlook`, {
        client_id: outlookCredentials.client_id,
        client_secret: outlookCredentials.client_secret || undefined,
        tenant_id: outlookCredentials.tenant_id || 'common',
        interval: parseInt(outlookCredentials.interval) || 30
      })
      alert(response.data.message || 'Outlook polling started! Check console for device code authentication.')
      fetchEmailPollingStatus()
    } catch (err) {
      alert('Failed to start Outlook polling: ' + (err.response?.data?.detail || err.message))
    } finally {
      setOutlookConnecting(false)
    }
  }

  const handleStopPolling = async () => {
    try {
      await axios.post(`${API_URL}/api/email/stop`)
      alert('Email polling stopped')
      fetchEmailPollingStatus()
    } catch (err) {
      alert('Failed to stop polling: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDisconnectGmail = async () => {
    if (!confirm('Are you sure you want to disconnect Gmail?')) return
    
    try {
      await axios.post(`${API_URL}/api/email/disconnect-gmail`)
      alert('Gmail disconnected successfully')
      fetchEmailPollingStatus()
    } catch (err) {
      alert('Failed to disconnect Gmail: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDisconnectOutlook = async () => {
    if (!confirm('Are you sure you want to disconnect Outlook?')) return
    
    try {
      await axios.post(`${API_URL}/api/email/disconnect-outlook`)
      alert('Outlook disconnected successfully')
      fetchEmailPollingStatus()
    } catch (err) {
      alert('Failed to disconnect Outlook: ' + (err.response?.data?.detail || err.message))
    }
  }

  // State for fetched emails
  const [fetchedEmails, setFetchedEmails] = useState([])

  const fetchFetchedEmails = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/email/fetched-emails?limit=20`)
      setFetchedEmails(response.data.emails || [])
    } catch (err) {
      console.error('Failed to fetch emails:', err)
    }
  }

  // Fetch emails when polling is active
  useEffect(() => {
    if (activeTab === 'connect' && emailPollingStatus?.polling_active) {
      fetchFetchedEmails()
      const interval = setInterval(() => {
        fetchFetchedEmails()
      }, 5000) // Fetch every 5 seconds when polling
      return () => clearInterval(interval)
    }
  }, [activeTab, emailPollingStatus?.polling_active])

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
      // Refresh dashboard if on that tab
      if (activeTab === 'dashboard') {
        fetchStatistics()
        fetchClassifications()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to classify email. Make sure the backend is running.')
      console.error('Classification error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setEmail({ subject: '', body: '', sender: '' })
    setResult(null)
    setError(null)
  }

  const handleUpdateRules = async (rules) => {
    try {
      await axios.post(`${API_URL}/api/process/rules`, rules)
      alert('Rules updated successfully!')
    } catch (err) {
      alert('Failed to update rules: ' + err.response?.data?.detail)
    }
  }

  const handleUpdateActionRules = async (rules) => {
    try {
      await axios.post(`${API_URL}/api/actions/rules`, rules)
      alert('Action rules updated successfully!')
      fetchActionRules()
    } catch (err) {
      alert('Failed to update action rules: ' + err.response?.data?.detail)
    }
  }

  // Authentication functions
  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUser(response.data)
      setIsAuthenticated(true)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } catch (err) {
      setIsAuthenticated(false)
      setToken(null)
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, loginForm)
      const newToken = response.data.access_token
      setToken(newToken)
      localStorage.setItem('token', newToken)
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
      setUser({ id: response.data.user_id, email: response.data.email })
      setIsAuthenticated(true)
      setShowAuthModal(false)
      setLoginForm({ email: '', password: '' })
    } catch (err) {
      alert('Login failed: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    try {
      await axios.post(`${API_URL}/api/auth/register`, registerForm)
      alert('Registration successful! Please login.')
      setRegisterForm({ email: '', password: '', full_name: '' })
      setAuthMode('login')
    } catch (err) {
      alert('Registration failed: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleLogout = () => {
    setToken(null)
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  // New feature functions
  const handleSearch = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/search`, {
        params: { query: searchQuery, category: searchCategory || undefined, limit: 100 },
        headers: { Authorization: `Bearer ${token}` }
      })
      setSearchResults(response.data.results || [])
    } catch (err) {
      console.error('Search failed:', err)
      alert('Search failed. Make sure you are logged in.')
    }
  }

  const fetchAnalytics = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/analytics/insights?days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setAnalytics(response.data)
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch analytics:', err)
      }
    }
  }

  const fetchCustomCategories = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/categories/custom`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCustomCategories(response.data.categories || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch custom categories:', err)
      }
    }
  }

  const handleExport = async (format) => {
    try {
      const url = `${API_URL}/api/export/${format}?limit=1000`
      // Create a temporary link to download with auth header
      const link = document.createElement('a')
      link.href = url
      link.download = `classifications_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(link)
      
      // Use fetch with auth header
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const downloadUrl = window.URL.createObjectURL(blob)
        link.href = downloadUrl
        link.click()
        window.URL.revokeObjectURL(downloadUrl)
        document.body.removeChild(link)
      } else {
        throw new Error('Export failed')
      }
    } catch (err) {
      alert('Export failed: ' + (err.message || 'Please make sure you are logged in'))
    }
  }

  const handleSubmitFeedback = async (classificationId, correctedCategory, notes) => {
    try {
      await axios.post(`${API_URL}/api/feedback`, {
        classification_id: classificationId,
        corrected_category: correctedCategory,
        notes: notes
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Feedback submitted successfully!')
      setShowFeedbackModal(false)
      fetchClassifications()
    } catch (err) {
      alert('Failed to submit feedback: ' + (err.response?.data?.detail || err.message))
    }
  }

  // Model Retraining functions
  const fetchRetrainingStatus = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/ml/retraining-status`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRetrainingStatus(response.data)
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch retraining status:', err)
      }
    }
  }

  const handleRetrainModel = async () => {
    if (!confirm('This will retrain the model with feedback data. Continue?')) return
    
    setRetrainingInProgress(true)
    try {
      const response = await axios.post(`${API_URL}/api/ml/retrain?use_feedback=true`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert(`Retraining ${response.data.success ? 'completed' : 'failed'}: ${response.data.message || response.data.error}`)
      fetchRetrainingStatus()
    } catch (err) {
      alert('Retraining failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setRetrainingInProgress(false)
    }
  }

  // Auto-Reply functions
  const fetchAutoReplyTemplates = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/auto-reply/templates`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setAutoReplyTemplates(response.data.templates || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch auto-reply templates:', err)
      }
    }
  }

  const handleCreateTemplate = async () => {
    if (!newTemplate.name || !newTemplate.subject || !newTemplate.body) {
      alert('Please fill in all required fields (Name, Subject, Body)')
      return
    }
    try {
      const keywords = newTemplate.keywords ? newTemplate.keywords.split(',').map(k => k.trim()).filter(k => k) : []
      await axios.post(`${API_URL}/api/auto-reply/templates`, {
        name: newTemplate.name,
        subject: newTemplate.subject,
        body: newTemplate.body,
        category_filter: newTemplate.category_filter || undefined,
        sender_filter: newTemplate.sender_filter || undefined,
        keywords: keywords.length > 0 ? keywords : undefined
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Template created successfully!')
      setShowTemplateModal(false)
      setNewTemplate({ name: '', subject: '', body: '', category_filter: '', sender_filter: '', keywords: [] })
      fetchAutoReplyTemplates()
    } catch (err) {
      alert('Failed to create template: ' + (err.response?.data?.detail || err.message || 'Unknown error'))
    }
  }

  // Email Scheduling functions
  const fetchScheduledEmails = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/schedule/emails`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setScheduledEmails(response.data.emails || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch scheduled emails:', err)
      }
    }
  }

  const handleScheduleEmail = async () => {
    if (!newScheduledEmail.recipient || !newScheduledEmail.subject || !newScheduledEmail.body || !newScheduledEmail.scheduled_time) {
      alert('Please fill in all required fields (Recipient, Subject, Body, Scheduled Time)')
      return
    }
    if (new Date(newScheduledEmail.scheduled_time) < new Date()) {
      alert('Scheduled time must be in the future')
      return
    }
    try {
      // Convert datetime-local to ISO format
      const scheduledTime = new Date(newScheduledEmail.scheduled_time).toISOString()
      await axios.post(`${API_URL}/api/schedule/email`, {
        recipient: newScheduledEmail.recipient,
        subject: newScheduledEmail.subject,
        body: newScheduledEmail.body,
        scheduled_time: scheduledTime
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Email scheduled successfully!')
      setShowScheduleModal(false)
      setNewScheduledEmail({ recipient: '', subject: '', body: '', scheduled_time: '' })
      fetchScheduledEmails()
    } catch (err) {
      alert('Failed to schedule email: ' + (err.response?.data?.detail || err.message || 'Unknown error'))
    }
  }

  // Calendar functions
  const fetchCalendarEvents = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/calendar/events`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCalendarEvents(response.data.events || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch calendar events:', err)
      }
    }
  }

  const handleExtractMeeting = async (emailSubject, emailBody, emailId) => {
    if (!token) {
      alert('Please login to use this feature')
      return
    }
    if (!emailSubject && !emailBody) {
      alert('No email content available to extract meeting from')
      return
    }
    try {
      const response = await axios.post(`${API_URL}/api/calendar/extract-meeting`, {
        email_subject: emailSubject || 'No Subject',
        email_body: emailBody || '',
        email_id: emailId
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.data.meeting_found) {
        alert('Meeting extracted and added to calendar!')
        fetchCalendarEvents()
      } else {
        alert('No meeting information found in this email.')
      }
    } catch (err) {
      alert('Failed to extract meeting: ' + (err.response?.data?.detail || err.message || 'Unknown error'))
    }
  }

  // Reports functions
  const fetchReportTemplates = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/reports/templates`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setReportTemplates(response.data.templates || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch report templates:', err)
      }
    }
  }

  const fetchGeneratedReports = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/reports/generated`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setGeneratedReports(response.data.reports || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch generated reports:', err)
      }
    }
  }

  const handleGenerateReport = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/reports/generate`, {
        report_type: 'classification',
        filters: {
          category: reportFilters.category || undefined,
          start_date: reportFilters.start_date || undefined,
          end_date: reportFilters.end_date || undefined,
          min_confidence: reportFilters.min_confidence || undefined,
          limit: 1000
        },
        format: 'text'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      // Show report in modal or download
      const reportContent = response.data.content
      const blob = new Blob([reportContent], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `report_${new Date().toISOString().split('T')[0]}.txt`
      link.click()
      window.URL.revokeObjectURL(url)
      
      alert(`Report generated with ${response.data.record_count} records!`)
      setShowReportModal(false)
      fetchGeneratedReports()
    } catch (err) {
      alert('Failed to generate report: ' + (err.response?.data?.detail || err.message))
    }
  }

  // Tasks functions
  const fetchTasks = async () => {
    if (!token) return
    try {
      const response = await axios.get(`${API_URL}/api/tasks`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTasks(response.data.tasks || [])
    } catch (err) {
      if (err.response?.status !== 401) {
        console.error('Failed to fetch tasks:', err)
      }
    }
  }

  const handleCreateTask = async () => {
    if (!newTask.email_subject) {
      alert('Please enter a task title')
      return
    }
    try {
      const dueDate = newTask.due_date ? new Date(newTask.due_date).toISOString() : undefined
      await axios.post(`${API_URL}/api/tasks/create-from-email`, {
        email_subject: newTask.email_subject,
        email_body: newTask.email_body || '',
        task_type: newTask.task_type,
        priority: newTask.priority,
        due_date: dueDate
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Task created successfully!')
      setShowTaskModal(false)
      setNewTask({ email_subject: '', email_body: '', task_type: 'general', priority: 'medium', due_date: '' })
      fetchTasks()
    } catch (err) {
      alert('Failed to create task: ' + (err.response?.data?.detail || err.message || 'Unknown error'))
    }
  }

  // Email marking functions
  const toggleStarEmail = (emailId) => {
    setEmailMarkings(prev => ({
      ...prev,
      [emailId]: {
        ...prev[emailId],
        starred: !prev[emailId]?.starred
      }
    }))
  }

  const toggleArchiveEmail = (emailId) => {
    setEmailMarkings(prev => ({
      ...prev,
      [emailId]: {
        ...prev[emailId],
        archived: !prev[emailId]?.archived
      }
    }))
  }

  const toggleReadStatus = (emailId) => {
    setEmailMarkings(prev => ({
      ...prev,
      [emailId]: {
        ...prev[emailId],
        read: !prev[emailId]?.read
      }
    }))
  }

  const deleteEmailMarking = (emailId) => {
    setEmailMarkings(prev => {
      const newMarkings = { ...prev }
      delete newMarkings[emailId]
      return newMarkings
    })
  }

  const getCategoryColor = (category) => {
    const colors = {
      spam: '#ef4444',
      important: '#3b82f6',
      promotion: '#f59e0b',
      social: '#10b981',
      updates: '#8b5cf6'
    }
    return colors[category] || '#6b7280'
  }

  const getDepartmentColor = (department) => {
    const colors = {
      Sales: '#3b82f6',
      HR: '#10b981',
      Finance: '#f59e0b',
      Support: '#8b5cf6',
      Marketing: '#ef4444',
      IT: '#6b7280'
    }
    return colors[department] || '#9ca3af'
  }

  // Department Routing functions
  const fetchRoutingStatus = async () => {
    setLoadingRouting(true)
    try {
      const response = await axios.get(`${API_URL}/api/departments/routing-status`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      setRoutingStatus(response.data)
    } catch (err) {
      console.error('Failed to fetch routing status:', err)
      // Set empty state if error
      setRoutingStatus({
        routing_status: {
          total_emails: 0,
          routed_emails: 0,
          non_routed_emails: 0,
          routing_percentage: 0,
          is_routing_active: false
        },
        department_distribution: {}
      })
    } finally {
      setLoadingRouting(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/departments`)
      setDepartments(response.data.departments || [])
    } catch (err) {
      console.error('Failed to fetch departments:', err)
      // Set empty array if error
      setDepartments([])
    }
  }

  const fetchDepartmentEmails = async (department) => {
    try {
      const response = await axios.get(`${API_URL}/api/departments/${department}/emails`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        params: { limit: 50 }
      })
      setDepartmentEmails(prev => ({
        ...prev,
        [department]: response.data.emails || []
      }))
    } catch (err) {
      console.error(`Failed to fetch emails for ${department}:`, err)
      setDepartmentEmails(prev => ({
        ...prev,
        [department]: []
      }))
    }
  }

  const fetchDepartmentsSummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/departments/summary/all`)
      setDepartmentsSummary(response.data)
    } catch (err) {
      console.error('Failed to fetch departments summary:', err)
      // Set empty state if error
      setDepartmentsSummary({ departments: {} })
    }
  }

  // Load routing data when routing tab is active
  useEffect(() => {
    if (activeTab === 'routing') {
      fetchRoutingStatus()
      fetchDepartments()
      fetchDepartmentsSummary()
    }
  }, [activeTab, token])

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
            <div>
              <h1>📧 AI Email Classifier</h1>
              <p>Final Year Project - Intelligent Email Classification System</p>
            </div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              {/* Dark Mode Toggle */}
              <button 
                onClick={() => setDarkMode(!darkMode)}
                style={{ 
                  padding: '0.5rem', 
                  background: darkMode ? '#fbbf24' : '#1f2937', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '8px', 
                  cursor: 'pointer',
                  fontSize: '1.2rem',
                  width: '40px',
                  height: '40px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title={`Toggle ${darkMode ? 'Light' : 'Dark'} Mode (Ctrl/Cmd + D)`}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
              
              {isAuthenticated ? (
                <>
                  <span style={{ color: 'white' }}>Welcome, {user?.email}</span>
                  <button onClick={handleLogout} style={{ padding: '0.5rem 1rem', background: '#ef4444', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    Logout
                  </button>
                </>
              ) : (
                <button onClick={() => { setShowAuthModal(true); setAuthMode('login') }} style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                  Login / Register
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Login/Register Modal */}
        {showAuthModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '400px', width: '90%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h2>{authMode === 'login' ? 'Login' : 'Register'}</h2>
                <button onClick={() => { setShowAuthModal(false); setLoginForm({ email: '', password: '' }); setRegisterForm({ email: '', password: '', full_name: '' }) }} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              
              {authMode === 'login' ? (
                <form onSubmit={handleLogin}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label>Email</label>
                    <input type="email" value={loginForm.email} onChange={(e) => setLoginForm({...loginForm, email: e.target.value})} required style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label>Password</label>
                    <input type="password" value={loginForm.password} onChange={(e) => setLoginForm({...loginForm, password: e.target.value})} required style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  <button type="submit" style={{ width: '100%', padding: '0.75rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Login</button>
                  <p style={{ textAlign: 'center', marginTop: '1rem' }}>
                    Don't have an account? <button type="button" onClick={() => setAuthMode('register')} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer' }}>Register</button>
                  </p>
                </form>
              ) : (
                <form onSubmit={handleRegister}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label>Full Name</label>
                    <input type="text" value={registerForm.full_name} onChange={(e) => setRegisterForm({...registerForm, full_name: e.target.value})} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label>Email</label>
                    <input type="email" value={registerForm.email} onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})} required style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label>Password</label>
                    <input type="password" value={registerForm.password} onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})} required style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }} />
                  </div>
                  <button type="submit" style={{ width: '100%', padding: '0.75rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Register</button>
                  <p style={{ textAlign: 'center', marginTop: '1rem' }}>
                    Already have an account? <button type="button" onClick={() => setAuthMode('login')} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer' }}>Login</button>
                  </p>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Sidebar Navigation */}
        <div className="app-layout">
          <div className="sidebar">
            <div className="tabs">
              <button 
                className={activeTab === 'classify' ? 'tab active' : 'tab'}
                onClick={() => setActiveTab('classify')}
              >
                📧 Classify Email
              </button>
              <button 
                className={activeTab === 'dashboard' ? 'tab active' : 'tab'}
                onClick={() => setActiveTab('dashboard')}
              >
                📊 Admin Dashboard
              </button>
              <button 
                className={activeTab === 'connect' ? 'tab active' : 'tab'}
                onClick={() => setActiveTab('connect')}
              >
                🔌 Email Connection
              </button>
              {/* Debug: Show auth status */}
              {!isAuthenticated && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#fef3c7', color: '#92400e', borderRadius: '8px', fontSize: '0.85rem', textAlign: 'center' }}>
                  ⚠️ Login to see new features
                </div>
              )}
              {isAuthenticated && (
                <>
                  <button 
                    className={activeTab === 'search' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('search')}
                  >
                    🔍 Search
                  </button>
                  <button 
                    className={activeTab === 'automation' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('automation')}
                  >
                    ⚙️ Automation
                  </button>
                  <button 
                    className={activeTab === 'calendar' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('calendar')}
                  >
                    📅 Calendar
                  </button>
                  <button 
                    className={activeTab === 'tasks' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('tasks')}
                  >
                    ✓ Tasks
                  </button>
                  <button 
                    className={activeTab === 'reports' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('reports')}
                  >
                    📊 Reports
                  </button>
                  <button 
                    className={activeTab === 'routing' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('routing')}
                  >
                    🏢 Department Routing
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Main Content Wrapper */}
          <div className="main-content-wrapper">

        {/* Classify Tab */}
        {activeTab === 'classify' && (
          <div className="main-content">
            <div className="form-container">
              <form onSubmit={handleSubmit} className="email-form">
                <div className="form-group">
                  <label htmlFor="subject">Subject</label>
                  <input
                    type="text"
                    id="subject"
                    value={email.subject}
                    onChange={(e) => setEmail({ ...email, subject: e.target.value })}
                    placeholder="Enter email subject..."
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="body">Body</label>
                  <textarea
                    id="body"
                    value={email.body}
                    onChange={(e) => setEmail({ ...email, body: e.target.value })}
                    placeholder="Enter email body text..."
                    rows="8"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="sender">Sender (Optional)</label>
                  <input
                    type="email"
                    id="sender"
                    value={email.sender}
                    onChange={(e) => setEmail({ ...email, sender: e.target.value })}
                    placeholder="sender@example.com"
                  />
                </div>

                <div className="form-actions">
                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? 'Classifying...' : 'Classify Email'}
                  </button>
                  <button type="button" className="btn-secondary" onClick={handleReset}>
                    Reset
                  </button>
                </div>
              </form>
            </div>

            <div className="result-container">
              {error && (
                <div className="error-message">
                  <strong>Error:</strong> {error}
                </div>
              )}

              {result && (
                <div className="result-card">
                  <h2>Classification Result</h2>
                  <div className="result-main">
                    <div 
                      className="category-badge"
                      style={{ backgroundColor: getCategoryColor(result.category) }}
                    >
                      {result.category.toUpperCase()}
                    </div>
                    <div className="confidence">
                      Confidence: {(result.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  {result.department && (
                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f0fdf4', borderRadius: '8px', borderLeft: `4px solid ${getDepartmentColor(result.department)}` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <strong>📬 Routed to Department:</strong>
                        <span 
                          style={{ 
                            padding: '0.25rem 0.75rem', 
                            background: getDepartmentColor(result.department), 
                            color: 'white', 
                            borderRadius: '6px',
                            fontWeight: 'bold'
                          }}
                        >
                          {result.department}
                        </span>
                      </div>
                      {result.department_info && (
                        <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                          {result.department_info.department_name} • {result.department_info.department_email}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="probabilities">
                    <h3>All Probabilities</h3>
                    <div className="probability-list">
                      {Object.entries(result.probabilities)
                        .sort((a, b) => b[1] - a[1])
                        .map(([category, prob]) => (
                          <div key={category} className="probability-item">
                            <span className="category-name">{category}</span>
                            <div className="progress-bar">
                              <div 
                                className="progress-fill"
                                style={{ 
                                  width: `${prob * 100}%`,
                                  backgroundColor: getCategoryColor(category)
                                }}
                              />
                            </div>
                            <span className="probability-value">{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {!result && !error && !loading && (
                <div className="placeholder">
                  <p>👆 Enter an email above and click "Classify Email" to see the results</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Email Connection Tab */}
        {activeTab === 'connect' && (
          <div className="connection-page">
            <div className="connection-container">
              {/* Connection Status Overview */}
              <div className="connection-status-card">
                <h2>📡 Connection Status</h2>
                <div className="status-overview">
                  <div className="status-badge">
                    <div className="badge-label">Gmail</div>
                    <div className={emailPollingStatus?.gmail_connected ? 'badge-status connected' : 'badge-status disconnected'}>
                      {emailPollingStatus?.gmail_connected ? '✅ Connected' : '❌ Not Connected'}
                    </div>
                  </div>
                  <div className="status-badge">
                    <div className="badge-label">Outlook</div>
                    <div className={emailPollingStatus?.outlook_connected ? 'badge-status connected' : 'badge-status disconnected'}>
                      {emailPollingStatus?.outlook_connected ? '✅ Connected' : '❌ Not Connected'}
                    </div>
                  </div>
                </div>

                {emailPollingStatus?.polling_active && (
                  <div className="active-polling-info">
                    <div className="polling-status-header">
                      <span className="pulse-dot"></span>
                      <strong>Polling Active</strong>
                    </div>
                    <div className="polling-details">
                      <div className="detail-item">
                        <span>Interval:</span>
                        <span>{emailPollingStatus.poll_interval}s</span>
                      </div>
                      <div className="detail-item">
                        <span>Processed:</span>
                        <span className="highlight">{emailPollingStatus.processed_count || 0}</span>
                      </div>
                      {emailPollingStatus.last_check_gmail && (
                        <div className="detail-item">
                          <span>Last Gmail Check:</span>
                          <span>{new Date(emailPollingStatus.last_check_gmail).toLocaleTimeString()}</span>
                        </div>
                      )}
                      {emailPollingStatus.last_check_outlook && (
                        <div className="detail-item">
                          <span>Last Outlook Check:</span>
                          <span>{new Date(emailPollingStatus.last_check_outlook).toLocaleTimeString()}</span>
                        </div>
                      )}
                    </div>
                    <button className="btn-stop-full" onClick={handleStopPolling}>
                      Stop Polling
                    </button>
                  </div>
                )}
              </div>

              {/* Gmail Connection */}
              <div className="provider-card">
                <div className="provider-header">
                  <h2>📧 Connect Gmail</h2>
                  <div className={emailPollingStatus?.gmail_connected ? 'provider-status connected' : 'provider-status disconnected'}>
                    {emailPollingStatus?.gmail_connected ? 'Connected' : 'Not Connected'}
                  </div>
                </div>
                
                {emailPollingStatus?.gmail_connected ? (
                  <div className="connection-info">
                    <div className="connection-success">
                      <div className="success-icon">✓</div>
                      <div className="success-content">
                        <h3>Gmail is connected and active</h3>
                        <p>Your Gmail account is successfully connected and ready to fetch emails.</p>
                        {emailPollingStatus?.polling_active && emailPollingStatus?.last_check_gmail && (
                          <div className="connection-details">
                            <div className="detail-row">
                              <span className="detail-label">Last check:</span>
                              <span className="detail-value">{new Date(emailPollingStatus.last_check_gmail).toLocaleTimeString()}</span>
                            </div>
                            <div className="detail-row">
                              <span className="detail-label">Poll interval:</span>
                              <span className="detail-value">{emailPollingStatus.poll_interval}s</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="provider-actions">
                      <button 
                        className="btn-disconnect-provider"
                        onClick={handleDisconnectGmail}
                      >
                        Disconnect Gmail
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="credentials-form">
                    <div className="form-group">
                      <label htmlFor="gmail-client-id">Client ID *</label>
                      <input
                        type="text"
                        id="gmail-client-id"
                        value={gmailCredentials.client_id}
                        onChange={(e) => setGmailCredentials({...gmailCredentials, client_id: e.target.value})}
                        placeholder="Enter Gmail Client ID"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="gmail-client-secret">Client Secret *</label>
                      <input
                        type="password"
                        id="gmail-client-secret"
                        value={gmailCredentials.client_secret}
                        onChange={(e) => setGmailCredentials({...gmailCredentials, client_secret: e.target.value})}
                        placeholder="Enter Gmail Client Secret"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="gmail-interval">Poll Interval (seconds)</label>
                      <input
                        type="number"
                        id="gmail-interval"
                        value={gmailCredentials.interval}
                        onChange={(e) => setGmailCredentials({...gmailCredentials, interval: e.target.value})}
                        min="10"
                        max="300"
                        placeholder="30"
                      />
                    </div>

                    <div className="provider-actions">
                      <button 
                        className="btn-connect-provider"
                        onClick={handleStartGmail}
                        disabled={gmailConnecting || emailPollingStatus?.polling_active}
                      >
                        {gmailConnecting ? 'Connecting...' : 'Connect Gmail'}
                      </button>
                    </div>

                    <div className="help-section">
                      <p><strong>How to get Gmail credentials:</strong></p>
                      <ol>
                        <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a></li>
                        <li>Create a project and enable Gmail API</li>
                        <li>Create OAuth 2.0 credentials (Desktop app type)</li>
                        <li>Copy Client ID and Client Secret</li>
                      </ol>
                    </div>
                  </div>
                )}
              </div>

              {/* Outlook Connection */}
              <div className="provider-card">
                <div className="provider-header">
                  <h2>📬 Connect Outlook</h2>
                  <div className={emailPollingStatus?.outlook_connected ? 'provider-status connected' : 'provider-status disconnected'}>
                    {emailPollingStatus?.outlook_connected ? 'Connected' : 'Not Connected'}
                  </div>
                </div>
                
                {emailPollingStatus?.outlook_connected ? (
                  <div className="connection-info">
                    <div className="connection-success">
                      <div className="success-icon">✓</div>
                      <div className="success-content">
                        <h3>Outlook is connected and active</h3>
                        <p>Your Outlook account is successfully connected and ready to fetch emails.</p>
                        {emailPollingStatus?.polling_active && emailPollingStatus?.last_check_outlook && (
                          <div className="connection-details">
                            <div className="detail-row">
                              <span className="detail-label">Last check:</span>
                              <span className="detail-value">{new Date(emailPollingStatus.last_check_outlook).toLocaleTimeString()}</span>
                            </div>
                            <div className="detail-row">
                              <span className="detail-label">Poll interval:</span>
                              <span className="detail-value">{emailPollingStatus.poll_interval}s</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="provider-actions">
                      <button 
                        className="btn-disconnect-provider"
                        onClick={handleDisconnectOutlook}
                      >
                        Disconnect Outlook
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="credentials-form">
                    <div className="form-group">
                      <label htmlFor="outlook-client-id">Client ID (Application ID) *</label>
                      <input
                        type="text"
                        id="outlook-client-id"
                        value={outlookCredentials.client_id}
                        onChange={(e) => setOutlookCredentials({...outlookCredentials, client_id: e.target.value})}
                        placeholder="Enter Outlook Application ID"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="outlook-client-secret">Client Secret (Optional)</label>
                      <input
                        type="password"
                        id="outlook-client-secret"
                        value={outlookCredentials.client_secret}
                        onChange={(e) => setOutlookCredentials({...outlookCredentials, client_secret: e.target.value})}
                        placeholder="Enter Client Secret (for service account)"
                      />
                      <small>Leave empty to use device code flow</small>
                    </div>

                    <div className="form-group">
                      <label htmlFor="outlook-tenant-id">Tenant ID</label>
                      <input
                        type="text"
                        id="outlook-tenant-id"
                        value={outlookCredentials.tenant_id}
                        onChange={(e) => setOutlookCredentials({...outlookCredentials, tenant_id: e.target.value})}
                        placeholder="common"
                      />
                      <small>Use "common" for personal accounts</small>
                    </div>

                    <div className="form-group">
                      <label htmlFor="outlook-interval">Poll Interval (seconds)</label>
                      <input
                        type="number"
                        id="outlook-interval"
                        value={outlookCredentials.interval}
                        onChange={(e) => setOutlookCredentials({...outlookCredentials, interval: e.target.value})}
                        min="10"
                        max="300"
                        placeholder="30"
                      />
                    </div>

                    <div className="provider-actions">
                      <button 
                        className="btn-connect-provider"
                        onClick={handleStartOutlook}
                        disabled={outlookConnecting || emailPollingStatus?.polling_active}
                      >
                        {outlookConnecting ? 'Connecting...' : 'Connect Outlook'}
                      </button>
                    </div>

                    <div className="help-section">
                      <p><strong>How to get Outlook credentials:</strong></p>
                      <ol>
                        <li>Go to <a href="https://portal.azure.com/" target="_blank" rel="noopener noreferrer">Azure Portal</a></li>
                        <li>Navigate to Azure Active Directory → App registrations</li>
                        <li>Register a new application</li>
                        <li>Copy Application (client) ID</li>
                        <li>Create a client secret (optional)</li>
                        <li>Configure API permissions: Mail.Read, Mail.ReadWrite</li>
                      </ol>
                    </div>
                  </div>
                )}
              </div>

              {/* Live Email Feed */}
              {emailPollingStatus?.polling_active && (
                <div className="provider-card">
                  <div className="provider-header">
                    <h2>📬 Live Email Feed</h2>
                    <div className="provider-status connected">
                      Fetching Live
                    </div>
                  </div>
                  
                  <div className="live-feed-content">
                    <div className="feed-stats-bar">
                      <div className="stat-badge">
                        <span className="stat-label">Total Fetched:</span>
                        <span className="stat-value">{fetchedEmails.length}</span>
                      </div>
                      <div className="stat-badge">
                        <span className="stat-label">Poll Interval:</span>
                        <span className="stat-value">{emailPollingStatus.poll_interval}s</span>
                      </div>
                      <div className="stat-badge">
                        <span className="stat-label">Status:</span>
                        <span className="stat-value pulse-dot-inline">Active</span>
                      </div>
                    </div>

                    <div className="fetched-emails-list">
                      <h3>Recently Fetched Emails</h3>
                      {fetchedEmails.length > 0 ? (
                        <div className="emails-container">
                          {fetchedEmails.map((email, idx) => (
                            <div key={email.id || idx} className="fetched-email-item">
                              <div className="email-header-row">
                                <div className="email-category-badge" style={{ backgroundColor: getCategoryColor(email.category) }}>
                                  {email.category.toUpperCase()}
                                </div>
                                <div className="email-confidence">
                                  {(email.confidence * 100).toFixed(0)}%
                                </div>
                                <div className="email-time">
                                  {new Date(email.timestamp).toLocaleTimeString()}
                                </div>
                              </div>
                              <div className="email-subject">{email.subject || 'No Subject'}</div>
                              <div className="email-sender">From: {email.sender || 'Unknown'}</div>
                              {email.department && (
                                <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>📬 Routed to:</span>
                                  <span 
                                    style={{ 
                                      padding: '0.25rem 0.5rem', 
                                      background: getDepartmentColor(email.department), 
                                      color: 'white', 
                                      borderRadius: '4px',
                                      fontSize: '0.75rem',
                                      fontWeight: 'bold'
                                    }}
                                  >
                                    {email.department}
                                  </span>
                                </div>
                              )}
                              {email.probabilities && Object.keys(email.probabilities).length > 0 && (
                                <div className="email-probabilities-mini">
                                  {Object.entries(email.probabilities)
                                    .sort((a, b) => b[1] - a[1])
                                    .slice(0, 3)
                                    .map(([cat, prob]) => (
                                      <span key={cat} className="prob-mini">
                                        {cat}: {(prob * 100).toFixed(0)}%
                                      </span>
                                    ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="no-emails-message">
                          <p>📭 No emails fetched yet</p>
                          <p className="hint">Emails will appear here as they are fetched and classified</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Admin Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="dashboard">
            <div className="dashboard-grid">
              {/* Statistics Section */}
              <div className="dashboard-card">
                <h2>📊 Statistics</h2>
                {statistics && (
                  <div className="stats-grid">
                    <div className="stat-item">
                      <div className="stat-value">{statistics.total_classifications}</div>
                      <div className="stat-label">Total Classifications</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">{(statistics.average_confidence * 100).toFixed(1)}%</div>
                      <div className="stat-label">Avg Confidence</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">{statistics.recent_activity_24h}</div>
                      <div className="stat-label">Last 24h</div>
                    </div>
                  </div>
                )}
                
                {statistics && statistics.category_distribution && (
                  <div className="category-stats">
                    <h3>Category Distribution</h3>
                    {Object.entries(statistics.category_distribution).map(([cat, count]) => (
                      <div key={cat} className="category-stat-item">
                        <span className="category-label">{cat}</span>
                        <div className="stat-bar">
                          <div 
                            className="stat-bar-fill"
                            style={{ 
                              width: `${(count / statistics.total_classifications) * 100}%`,
                              backgroundColor: getCategoryColor(cat)
                            }}
                          />
                        </div>
                        <span className="category-count">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recent Classifications */}
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                  <h2>📋 Recent Classifications</h2>
                  {isAuthenticated && (
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button onClick={() => handleExport('csv')} style={{ padding: '0.5rem 1rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' }}>
                        📥 CSV
                      </button>
                      <button onClick={() => handleExport('json')} style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' }}>
                        📥 JSON
                      </button>
                    </div>
                  )}
                </div>
                <div className="classifications-list">
                  {classifications.slice(0, 10)
                    .filter(c => !emailMarkings[c.id]?.archived)
                    .map((classification, idx) => {
                      const emailId = classification.id || `email-${idx}`
                      const marking = emailMarkings[emailId] || {}
                      return (
                    <div 
                      key={idx} 
                      className={`classification-item ${marking.archived ? 'archived' : ''} ${!marking.read ? 'unread' : ''}`}
                      style={{ opacity: marking.archived ? 0.6 : 1 }}
                    >
                      <div className="classification-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          {/* Star Button */}
                          <button
                            onClick={() => toggleStarEmail(emailId)}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '1.2rem',
                              padding: '0',
                              color: marking.starred ? '#fbbf24' : '#9ca3af'
                            }}
                            title={marking.starred ? 'Unstar' : 'Star'}
                          >
                            {marking.starred ? '⭐' : '☆'}
                          </button>
                          {/* Read/Unread Button */}
                          <button
                            onClick={() => toggleReadStatus(emailId)}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.9rem',
                              padding: '0',
                              color: marking.read ? '#6b7280' : '#3b82f6'
                            }}
                            title={marking.read ? 'Mark as unread' : 'Mark as read'}
                          >
                            {marking.read ? '📧' : '📬'}
                          </button>
                          <span 
                            className="classification-badge-small"
                            style={{ backgroundColor: getCategoryColor(classification.category) }}
                          >
                            {classification.category}
                          </span>
                          {classification.department && (
                            <span 
                              style={{ 
                                padding: '0.25rem 0.5rem', 
                                background: getDepartmentColor(classification.department), 
                                color: 'white', 
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 'bold'
                              }}
                            >
                              {classification.department}
                            </span>
                          )}
                        </div>
                        <span className="classification-confidence">
                          {(classification.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="classification-subject">{classification.email_subject}</div>
                      <div className="classification-meta">
                        {classification.email_sender} • {new Date(classification.timestamp).toLocaleString()}
                      </div>
                      {isAuthenticated && (
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                          <button 
                            onClick={() => { setSelectedClassification(classification); setShowFeedbackModal(true) }}
                            style={{ padding: '0.25rem 0.5rem', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                          >
                            ✏️ Correct
                          </button>
                          {/* Archive Button */}
                          <button 
                            onClick={() => toggleArchiveEmail(emailId)}
                            style={{ padding: '0.25rem 0.5rem', background: marking.archived ? '#10b981' : '#6b7280', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                            title={marking.archived ? 'Unarchive' : 'Archive'}
                          >
                            {marking.archived ? '📦 Unarchive' : '📦 Archive'}
                          </button>
                          <button 
                            onClick={() => handleExtractMeeting(
                              classification.email_subject || 'No Subject', 
                              classification.email_body || classification.body || '', 
                              classification.id
                            )}
                            style={{ padding: '0.25rem 0.5rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                          >
                            📅 Extract Meeting
                          </button>
                          <button 
                            onClick={() => {
                              setNewTask({
                                email_subject: classification.email_subject || 'No Subject',
                                email_body: classification.email_body || classification.body || '',
                                task_type: 'general',
                                priority: classification.category === 'important' ? 'high' : 'medium',
                                due_date: ''
                              })
                              setShowTaskModal(true)
                            }}
                            style={{ padding: '0.25rem 0.5rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                          >
                            ✓ Create Task
                          </button>
                        </div>
                      )}
                    </div>
                      )
                    })}
                </div>
              </div>

              {/* Monitoring Data */}
              <div className="dashboard-card">
                <h2>🔍 Real-Time Monitoring</h2>
                {monitoring && (
                  <div className="monitoring-data">
                    <div className="monitoring-item">
                      <strong>Last Update:</strong> {new Date(monitoring.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="monitoring-item">
                      <strong>System Status:</strong> <span className="status-healthy">Healthy</span>
                    </div>
                    <div className="monitoring-item">
                      <strong>Recent Activity:</strong> {monitoring.statistics?.recent_activity_24h || 0} emails
                    </div>
                  </div>
                )}
              </div>

              {/* Rule Control */}
              <div className="dashboard-card">
                <h2>⚙️ Control Rules</h2>
                <div className="rules-section">
                  <h3>Action Rules</h3>
                  <div className="rules-list">
                    {Object.entries(actionRules).map(([category, rule]) => (
                      <div key={category} className="rule-item">
                        <div className="rule-header">
                          <strong>{category}</strong>
                        </div>
                        <div className="rule-details">
                          Route: {rule.route} | Tag: {rule.tag} | Priority: {rule.priority}
                        </div>
                      </div>
                    ))}
                  </div>
                  <button 
                    className="btn-secondary"
                    onClick={() => alert('Rule editor coming soon! Use API endpoint to update rules.')}
                  >
                    Edit Rules
                  </button>
                </div>
              </div>

              {/* Analytics (Authenticated Users Only) */}
              {isAuthenticated && analytics && (
                <div className="dashboard-card">
                  <h2>📈 Email Insights</h2>
                  {analytics.top_senders && analytics.top_senders.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h3>Top Senders</h3>
                      {analytics.top_senders.slice(0, 5).map((sender, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: '#f9fafb', borderRadius: '4px', marginBottom: '0.25rem' }}>
                          <span>{sender.sender}</span>
                          <span style={{ fontWeight: 'bold' }}>{sender.count} emails</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {analytics.peak_hour !== null && (
                    <div>
                      <h3>Peak Hour</h3>
                      <p>Most emails received at: <strong>{analytics.peak_hour}:00</strong></p>
                    </div>
                  )}
                </div>
              )}

              {/* Custom Categories (Authenticated Users Only) */}
              {isAuthenticated && (
                <div className="dashboard-card">
                  <h2>🏷️ Custom Categories</h2>
                  {customCategories.length > 0 ? (
                    <div>
                      {customCategories.map((cat) => (
                        <div key={cat.id} style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                          <strong>{cat.category_name}</strong>
                          {cat.description && <p style={{ margin: '0.25rem 0', color: '#6b7280' }}>{cat.description}</p>}
                          <span style={{ fontSize: '0.9rem', color: '#6b7280' }}>{cat.training_samples} samples</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#6b7280' }}>No custom categories yet. Create one using the API.</p>
                  )}
                </div>
              )}

              {/* Model Retraining (Authenticated Users Only) */}
              {isAuthenticated && retrainingStatus && (
                <div className="dashboard-card">
                  <h2>🤖 Model Retraining</h2>
                  <div style={{ marginBottom: '1rem' }}>
                    <p><strong>Feedback Samples:</strong> {retrainingStatus.feedback_samples || 0}</p>
                    <p><strong>High Confidence Samples:</strong> {retrainingStatus.high_confidence_samples || 0}</p>
                    <p><strong>Ready for Retraining:</strong> {retrainingStatus.ready_for_retraining ? '✅ Yes' : '❌ No (need at least 10 feedback samples)'}</p>
                    {retrainingStatus.model_last_modified && (
                      <p><strong>Last Retrained:</strong> {new Date(retrainingStatus.model_last_modified).toLocaleString()}</p>
                    )}
                  </div>
                  <button
                    onClick={handleRetrainModel}
                    disabled={retrainingInProgress || !retrainingStatus.ready_for_retraining}
                    style={{
                      padding: '0.75rem 1.5rem',
                      background: retrainingStatus.ready_for_retraining ? '#10b981' : '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: retrainingStatus.ready_for_retraining ? 'pointer' : 'not-allowed'
                    }}
                  >
                    {retrainingInProgress ? 'Retraining...' : 'Retrain Model'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && isAuthenticated && (
          <div className="main-content">
            <div className="dashboard-card">
              <h2>🔍 Search Classifications</h2>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  placeholder="Search by subject, sender, or body..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ flex: 1, minWidth: '200px', padding: '0.75rem', borderRadius: '8px', border: '1px solid #ccc' }}
                />
                <select
                  value={searchCategory}
                  onChange={(e) => setSearchCategory(e.target.value)}
                  style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #ccc' }}
                >
                  <option value="">All Categories</option>
                  <option value="spam">Spam</option>
                  <option value="important">Important</option>
                  <option value="promotion">Promotion</option>
                  <option value="social">Social</option>
                  <option value="updates">Updates</option>
                </select>
                <button
                  onClick={handleSearch}
                  style={{ padding: '0.75rem 1.5rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Search
                </button>
              </div>

              {searchResults.length > 0 && (
                <div>
                  <h3>Results ({searchResults.length})</h3>
                  <div className="classifications-list">
                    {searchResults.map((classification, idx) => (
                      <div key={idx} className="classification-item">
                        <div className="classification-header">
                          <span 
                            className="classification-badge-small"
                            style={{ backgroundColor: getCategoryColor(classification.category) }}
                          >
                            {classification.category}
                          </span>
                          <span className="classification-confidence">
                            {(classification.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="classification-subject">{classification.email_subject}</div>
                        <div className="classification-meta">
                          {classification.email_sender} • {new Date(classification.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Automation Tab */}
        {activeTab === 'automation' && isAuthenticated && (
          <div className="main-content">
            <div className="dashboard-grid">
              {/* Auto-Reply Templates */}
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2>📧 Auto-Reply Templates</h2>
                  <button
                    onClick={() => setShowTemplateModal(true)}
                    style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    + New Template
                  </button>
                </div>
                {autoReplyTemplates.length > 0 ? (
                  <div>
                    {autoReplyTemplates.map((template) => (
                      <div key={template.id} style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                          <div>
                            <strong>{template.name}</strong>
                            <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>Subject: {template.subject}</p>
                            {template.category_filter && <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Category: {template.category_filter}</span>}
                            <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: template.is_active ? '#10b981' : '#ef4444' }}>
                              {template.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#6b7280' }}>No auto-reply templates yet. Create one to start automating responses.</p>
                )}
              </div>

              {/* Email Scheduling */}
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2>⏰ Scheduled Emails</h2>
                  <button
                    onClick={() => setShowScheduleModal(true)}
                    style={{ padding: '0.5rem 1rem', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    + Schedule Email
                  </button>
                </div>
                {scheduledEmails.length > 0 ? (
                  <div>
                    {scheduledEmails.filter(e => e.status === 'pending').map((email) => (
                      <div key={email.id} style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                        <strong>{email.subject}</strong>
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>To: {email.recipient}</p>
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                          Scheduled: {new Date(email.scheduled_time).toLocaleString()}
                        </p>
                        <span style={{ fontSize: '0.8rem', color: email.status === 'pending' ? '#f59e0b' : '#10b981' }}>
                          {email.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#6b7280' }}>No scheduled emails. Schedule an email to send it later.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Calendar Tab */}
        {activeTab === 'calendar' && isAuthenticated && (
          <div className="main-content">
            <div className="dashboard-card">
              <h2>📅 Calendar Events</h2>
              {calendarEvents.length > 0 ? (
                <div>
                  {calendarEvents.map((event) => (
                    <div key={event.id} style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                      <strong>{event.event_title}</strong>
                      {event.start_time && (
                        <p style={{ margin: '0.25rem 0', color: '#6b7280' }}>
                          {new Date(event.start_time).toLocaleString()}
                        </p>
                      )}
                      {event.location && (
                        <p style={{ margin: '0.25rem 0', color: '#6b7280' }}>📍 {event.location}</p>
                      )}
                      {event.attendees && event.attendees.length > 0 && (
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                          Attendees: {event.attendees.join(', ')}
                        </p>
                      )}
                      <span style={{ fontSize: '0.8rem', color: event.synced ? '#10b981' : '#6b7280' }}>
                        {event.synced ? '✅ Synced' : '⏳ Not synced'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#6b7280' }}>No calendar events yet. Extract meetings from emails to add them to your calendar.</p>
              )}
            </div>
          </div>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && isAuthenticated && (
          <div className="main-content">
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2>✓ Tasks</h2>
                  <button
                    onClick={() => setShowTaskModal(true)}
                    style={{ padding: '0.5rem 1rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    + Create Task
                  </button>
                </div>
                {tasks.length > 0 ? (
                  <div>
                    {tasks.filter(t => t.status !== 'completed').map((task) => (
                      <div key={task.id} style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                          <div style={{ flex: 1 }}>
                            <strong>{task.task_title}</strong>
                            {task.task_description && (
                              <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                                {task.task_description.substring(0, 100)}...
                              </p>
                            )}
                            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.8rem' }}>
                              <span style={{ color: '#6b7280' }}>Type: {task.task_type}</span>
                              <span style={{ color: '#6b7280' }}>Priority: {task.priority}</span>
                              {task.due_date && (
                                <span style={{ color: '#6b7280' }}>
                                  Due: {new Date(task.due_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                          <span style={{
                            fontSize: '0.8rem',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            background: task.status === 'pending' ? '#f59e0b' : '#10b981',
                            color: 'white'
                          }}>
                            {task.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#6b7280' }}>No tasks yet. Create tasks from emails to manage your workflow.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && isAuthenticated && (
          <div className="main-content">
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2>📊 Custom Reports</h2>
                  <button
                    onClick={() => setShowReportModal(true)}
                    style={{ padding: '0.5rem 1rem', background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Generate Report
                  </button>
                </div>
                
                {generatedReports.length > 0 ? (
                  <div>
                    <h3>Recent Reports</h3>
                    {generatedReports.slice(0, 5).map((report) => (
                      <div key={report.id} style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                        <strong>Report #{report.id}</strong>
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                          Type: {report.report_type} | Format: {report.format}
                        </p>
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                          Generated: {new Date(report.generated_at).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#6b7280' }}>No reports generated yet. Generate a report to analyze your email classifications.</p>
                )}
              </div>

              {reportTemplates.length > 0 && (
                <div className="dashboard-card">
                  <h2>📋 Report Templates</h2>
                  {reportTemplates.map((template) => (
                    <div key={template.id} style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '0.5rem' }}>
                      <strong>{template.name}</strong>
                      {template.description && (
                        <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>{template.description}</p>
                      )}
                      <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Type: {template.report_type} | Format: {template.format}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Feedback Modal */}
        {showFeedbackModal && selectedClassification && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '500px', width: '90%' }}>
              <h2>Submit Feedback</h2>
              <p><strong>Original Classification:</strong> {selectedClassification.category} ({(selectedClassification.confidence * 100).toFixed(1)}%)</p>
              <p><strong>Subject:</strong> {selectedClassification.email_subject}</p>
              
              <div style={{ marginTop: '1rem' }}>
                <label>Corrected Category</label>
                <select
                  id="correctedCategory"
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="spam">Spam</option>
                  <option value="important">Important</option>
                  <option value="promotion">Promotion</option>
                  <option value="social">Social</option>
                  <option value="updates">Updates</option>
                </select>
              </div>
              
              <div style={{ marginTop: '1rem' }}>
                <label>Notes (Optional)</label>
                <textarea
                  id="feedbackNotes"
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc', minHeight: '80px' }}
                  placeholder="Any additional notes..."
                />
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  onClick={() => {
                    const correctedCategory = document.getElementById('correctedCategory').value
                    const notes = document.getElementById('feedbackNotes').value
                    handleSubmitFeedback(selectedClassification.id, correctedCategory, notes)
                  }}
                  style={{ flex: 1, padding: '0.75rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Submit Feedback
                </button>
                <button
                  onClick={() => { setShowFeedbackModal(false); setSelectedClassification(null) }}
                  style={{ flex: 1, padding: '0.75rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Auto-Reply Template Modal */}
        {showTemplateModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '600px', width: '90%', maxHeight: '90vh', overflow: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h2>Create Auto-Reply Template</h2>
                <button onClick={() => setShowTemplateModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label>Template Name *</label>
                <input
                  type="text"
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate({...newTemplate, name: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="e.g., Out of Office"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Subject *</label>
                <input
                  type="text"
                  value={newTemplate.subject}
                  onChange={(e) => setNewTemplate({...newTemplate, subject: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="Re: {subject}"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Body *</label>
                <textarea
                  value={newTemplate.body}
                  onChange={(e) => setNewTemplate({...newTemplate, body: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc', minHeight: '120px' }}
                  placeholder="Thank you for your email..."
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Category Filter (Optional)</label>
                <select
                  value={newTemplate.category_filter}
                  onChange={(e) => setNewTemplate({...newTemplate, category_filter: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="">All Categories</option>
                  <option value="spam">Spam</option>
                  <option value="important">Important</option>
                  <option value="promotion">Promotion</option>
                  <option value="social">Social</option>
                  <option value="updates">Updates</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Sender Filter (Optional)</label>
                <input
                  type="text"
                  value={newTemplate.sender_filter}
                  onChange={(e) => setNewTemplate({...newTemplate, sender_filter: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="email@domain.com"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Keywords (Optional, comma-separated)</label>
                <input
                  type="text"
                  value={newTemplate.keywords}
                  onChange={(e) => setNewTemplate({...newTemplate, keywords: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="urgent, meeting, invoice"
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  onClick={handleCreateTemplate}
                  style={{ flex: 1, padding: '0.75rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Create Template
                </button>
                <button
                  onClick={() => setShowTemplateModal(false)}
                  style={{ flex: 1, padding: '0.75rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Schedule Email Modal */}
        {showScheduleModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '600px', width: '90%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h2>Schedule Email</h2>
                <button onClick={() => setShowScheduleModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label>Recipient *</label>
                <input
                  type="email"
                  value={newScheduledEmail.recipient}
                  onChange={(e) => setNewScheduledEmail({...newScheduledEmail, recipient: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="recipient@example.com"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Subject *</label>
                <input
                  type="text"
                  value={newScheduledEmail.subject}
                  onChange={(e) => setNewScheduledEmail({...newScheduledEmail, subject: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="Email subject"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Body *</label>
                <textarea
                  value={newScheduledEmail.body}
                  onChange={(e) => setNewScheduledEmail({...newScheduledEmail, body: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc', minHeight: '120px' }}
                  placeholder="Email body..."
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Scheduled Time *</label>
                <input
                  type="datetime-local"
                  value={newScheduledEmail.scheduled_time}
                  onChange={(e) => setNewScheduledEmail({...newScheduledEmail, scheduled_time: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  onClick={handleScheduleEmail}
                  style={{ flex: 1, padding: '0.75rem', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Schedule Email
                </button>
                <button
                  onClick={() => setShowScheduleModal(false)}
                  style={{ flex: 1, padding: '0.75rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Report Generator Modal */}
        {showReportModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '600px', width: '90%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h2>Generate Custom Report</h2>
                <button onClick={() => setShowReportModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label>Category Filter</label>
                <select
                  value={reportFilters.category}
                  onChange={(e) => setReportFilters({...reportFilters, category: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="">All Categories</option>
                  <option value="spam">Spam</option>
                  <option value="important">Important</option>
                  <option value="promotion">Promotion</option>
                  <option value="social">Social</option>
                  <option value="updates">Updates</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Start Date</label>
                <input
                  type="date"
                  value={reportFilters.start_date}
                  onChange={(e) => setReportFilters({...reportFilters, start_date: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>End Date</label>
                <input
                  type="date"
                  value={reportFilters.end_date}
                  onChange={(e) => setReportFilters({...reportFilters, end_date: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Minimum Confidence: {(reportFilters.min_confidence * 100).toFixed(0)}%</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={reportFilters.min_confidence}
                  onChange={(e) => setReportFilters({...reportFilters, min_confidence: parseFloat(e.target.value)})}
                  style={{ width: '100%', marginTop: '0.5rem' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  onClick={handleGenerateReport}
                  style={{ flex: 1, padding: '0.75rem', background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Generate Report
                </button>
                <button
                  onClick={() => setShowReportModal(false)}
                  style={{ flex: 1, padding: '0.75rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Task Modal */}
        {showTaskModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', maxWidth: '600px', width: '90%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h2>Create Task from Email</h2>
                <button onClick={() => setShowTaskModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label>Task Title *</label>
                <input
                  type="text"
                  value={newTask.email_subject}
                  onChange={(e) => setNewTask({...newTask, email_subject: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                  placeholder="Task title"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Task Description</label>
                <textarea
                  value={newTask.email_body}
                  onChange={(e) => setNewTask({...newTask, email_body: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc', minHeight: '100px' }}
                  placeholder="Task description..."
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Task Type</label>
                <select
                  value={newTask.task_type}
                  onChange={(e) => setNewTask({...newTask, task_type: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="general">General</option>
                  <option value="urgent">Urgent</option>
                  <option value="follow-up">Follow-up</option>
                  <option value="review">Review</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Priority</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask({...newTask, priority: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label>Due Date (Optional)</label>
                <input
                  type="datetime-local"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask({...newTask, due_date: e.target.value})}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  onClick={handleCreateTask}
                  style={{ flex: 1, padding: '0.75rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Create Task
                </button>
                <button
                  onClick={() => setShowTaskModal(false)}
                  style={{ flex: 1, padding: '0.75rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Department Routing Tab */}
        {activeTab === 'routing' && (
          <div className="main-content">
            <div className="dashboard-grid">
              {/* Routing Status Overview */}
              <div className="dashboard-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h2>📊 Routing Status</h2>
                  <button
                    onClick={fetchRoutingStatus}
                    disabled={loadingRouting}
                    style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' }}
                  >
                    {loadingRouting ? 'Refreshing...' : '🔄 Refresh'}
                  </button>
                </div>
                {routingStatus ? (
                  <div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                      <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
                          {routingStatus.routing_status?.total_emails || 0}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>Total Emails</div>
                      </div>
                      <div style={{ padding: '1rem', background: '#f0fdf4', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
                          {routingStatus.routing_status?.routed_emails || 0}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>Routed</div>
                      </div>
                      <div style={{ padding: '1rem', background: '#fef2f2', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ef4444' }}>
                          {routingStatus.routing_status?.non_routed_emails || 0}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>Not Routed</div>
                      </div>
                      <div style={{ padding: '1rem', background: '#fef3c7', borderRadius: '8px', textAlign: 'center' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
                          {routingStatus.routing_status?.routing_percentage?.toFixed(1) || 0}%
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>Routing Rate</div>
                      </div>
                    </div>
                    
                    <div style={{ marginBottom: '1rem', padding: '0.75rem', background: routingStatus.routing_status?.is_routing_active ? '#f0fdf4' : '#fef2f2', borderRadius: '8px' }}>
                      <strong>Status: </strong>
                      <span style={{ color: routingStatus.routing_status?.is_routing_active ? '#10b981' : '#ef4444' }}>
                        {routingStatus.routing_status?.is_routing_active ? '✅ Routing Active' : '❌ Routing Inactive'}
                      </span>
                    </div>

                    {routingStatus.department_distribution && Object.keys(routingStatus.department_distribution).length > 0 && (
                      <div>
                        <h3>Department Distribution</h3>
                        {Object.entries(routingStatus.department_distribution).map(([dept, count]) => (
                          <div key={dept} style={{ marginBottom: '0.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                              <span style={{ fontWeight: 'bold' }}>{dept}</span>
                              <span>{count} emails</span>
                            </div>
                            <div style={{ height: '8px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                              <div 
                                style={{ 
                                  height: '100%', 
                                  width: `${(count / (routingStatus.routing_status?.routed_emails || 1)) * 100}%`,
                                  background: getDepartmentColor(dept),
                                  transition: 'width 0.3s'
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : loadingRouting ? (
                  <p style={{ color: '#6b7280' }}>Loading routing status...</p>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                    <p>📊 No routing data available</p>
                    <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                      Classify some emails first to see routing statistics
                    </p>
                  </div>
                )}
              </div>

              {/* Departments Summary */}
              <div className="dashboard-card">
                <h2>🏢 Departments Overview</h2>
                {departmentsSummary && departmentsSummary.departments ? (
                  <div>
                    {Object.entries(departmentsSummary.departments).map(([deptKey, deptData]) => (
                      <div 
                        key={deptKey} 
                        style={{ 
                          padding: '1rem', 
                          background: '#f9fafb', 
                          borderRadius: '8px', 
                          marginBottom: '1rem',
                          borderLeft: `4px solid ${getDepartmentColor(deptKey)}`
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                          <div>
                            <h3 style={{ margin: 0, color: getDepartmentColor(deptKey) }}>{deptData.name || deptKey}</h3>
                            <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.9rem' }}>
                              {deptData.description || deptData.email}
                            </p>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: getDepartmentColor(deptKey) }}>
                              {deptData.total || 0}
                            </div>
                            <div style={{ color: '#6b7280', fontSize: '0.8rem' }}>emails</div>
                          </div>
                        </div>
                        {deptData.categories && Object.keys(deptData.categories).length > 0 && (
                          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#6b7280' }}>
                            <strong>Categories: </strong>
                            {Object.entries(deptData.categories).map(([cat, count]) => (
                              <span key={cat} style={{ marginRight: '0.5rem' }}>
                                {cat} ({count})
                              </span>
                            ))}
                          </div>
                        )}
                        <button
                          onClick={() => {
                            setSelectedDepartment(deptKey)
                            fetchDepartmentEmails(deptKey)
                          }}
                          style={{ 
                            marginTop: '0.5rem', 
                            padding: '0.5rem 1rem', 
                            background: getDepartmentColor(deptKey), 
                            color: 'white', 
                            border: 'none', 
                            borderRadius: '6px', 
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                          }}
                        >
                          View Emails →
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                    <p>🏢 No departments data available</p>
                    <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                      {departments.length === 0 ? 'Unable to load departments. Please check your connection.' : 'Loading departments summary...'}
                    </p>
                  </div>
                )}
              </div>

              {/* Department Emails */}
              {selectedDepartment && (
                <div className="dashboard-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2>📧 {selectedDepartment} Emails</h2>
                    <button
                      onClick={() => setSelectedDepartment(null)}
                      style={{ padding: '0.5rem 1rem', background: '#6b7280', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem' }}
                    >
                      ← Back
                    </button>
                  </div>
                  {departmentEmails[selectedDepartment] ? (
                    <div className="classifications-list">
                      {departmentEmails[selectedDepartment].length > 0 ? (
                        departmentEmails[selectedDepartment].map((email, idx) => (
                          <div key={email.id || idx} className="classification-item">
                            <div className="classification-header">
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span 
                                  className="classification-badge-small"
                                  style={{ backgroundColor: getCategoryColor(email.category) }}
                                >
                                  {email.category}
                                </span>
                                <span 
                                  style={{ 
                                    padding: '0.25rem 0.5rem', 
                                    background: getDepartmentColor(email.department), 
                                    color: 'white', 
                                    borderRadius: '4px',
                                    fontSize: '0.75rem'
                                  }}
                                >
                                  {email.department}
                                </span>
                              </div>
                              <span className="classification-confidence">
                                {(email.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="classification-subject">{email.email_subject || 'No Subject'}</div>
                            <div className="classification-meta">
                              {email.email_sender} • {new Date(email.timestamp).toLocaleString()}
                            </div>
                          </div>
                        ))
                      ) : (
                        <p style={{ color: '#6b7280' }}>No emails found for this department.</p>
                      )}
                    </div>
                  ) : (
                    <p style={{ color: '#6b7280' }}>Loading emails...</p>
                  )}
                </div>
              )}

              {/* All Departments List */}
              {!selectedDepartment && (
                <div className="dashboard-card">
                  <h2>📋 All Departments</h2>
                  {departments.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                      {departments.map((dept) => (
                        <div 
                          key={dept.name}
                          style={{ 
                            padding: '1rem', 
                            background: '#f9fafb', 
                            borderRadius: '8px',
                            border: `2px solid ${getDepartmentColor(dept.name)}`,
                            cursor: 'pointer',
                            transition: 'transform 0.2s',
                          }}
                          onClick={() => {
                            setSelectedDepartment(dept.name)
                            fetchDepartmentEmails(dept.name)
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                        >
                          <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                            {(dept.name === 'Sales' || dept.name === 'sales') && '💼'}
                            {(dept.name === 'HR' || dept.name === 'hr') && '👥'}
                            {(dept.name === 'Finance' || dept.name === 'finance') && '💰'}
                            {(dept.name === 'Support' || dept.name === 'support') && '🛟'}
                            {(dept.name === 'Marketing' || dept.name === 'marketing') && '📢'}
                            {(dept.name === 'IT' || dept.name === 'IT/Admin') && '💻'}
                          </div>
                          <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>{dept.name}</div>
                          <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{dept.description}</div>
                          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>{dept.email}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                      <p>📋 No departments loaded</p>
                      <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                        Make sure the backend is running and try refreshing.
                      </p>
                      <button
                        onClick={() => {
                          fetchDepartments()
                          fetchDepartmentsSummary()
                        }}
                        style={{ 
                          marginTop: '1rem', 
                          padding: '0.5rem 1rem', 
                          background: '#3b82f6', 
                          color: 'white', 
                          border: 'none', 
                          borderRadius: '6px', 
                          cursor: 'pointer',
                          fontSize: '0.9rem'
                        }}
                      >
                        🔄 Retry
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

          </div>
        </div>
      </div>
    </div>
  )
}

export default App
