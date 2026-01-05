import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [loading, setLoading] = useState(true)

    // Configure axios defaults
    // Configure axios defaults
    const API_URL = import.meta.env.VITE_API_URL || ''

    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
            checkAuth()
        } else {
            delete axios.defaults.headers.common['Authorization']
            setLoading(false)
        }
    }, [token])

    const checkAuth = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/auth/me`)
            setUser(response.data)
            setIsAuthenticated(true)
        } catch (err) {
            console.error('Auth check failed:', err)
            logout()
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        try {
            const response = await axios.post(`${API_URL}/api/auth/login`, { email, password })
            const newToken = response.data.access_token

            localStorage.setItem('token', newToken)
            setToken(newToken)
            setUser({ id: response.data.user_id, email: response.data.email })
            setIsAuthenticated(true)
            return { success: true }
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message || 'Login failed'
            }
        }
    }

    const register = async (email, password, fullName) => {
        try {
            await axios.post(`${API_URL}/api/auth/register`, {
                email,
                password,
                full_name: fullName
            })
            return { success: true }
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message || 'Registration failed'
            }
        }
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
        setIsAuthenticated(false)
        delete axios.defaults.headers.common['Authorization']
    }

    const value = {
        user,
        token,
        isAuthenticated,
        loading,
        login,
        register,
        logout,
        API_URL
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}
