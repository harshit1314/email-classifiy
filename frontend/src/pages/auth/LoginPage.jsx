import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Mail, Lock, Loader2, Eye, EyeOff, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const LoginPage = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [emailFocused, setEmailFocused] = useState(false)
    const [passwordFocused, setPasswordFocused] = useState(false)
    const [successMessage, setSuccessMessage] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(''), 5000)
            return () => clearTimeout(timer)
        }
    }, [error])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        // Basic validation
        if (!email || !password) {
            setError('Please fill in all fields')
            setLoading(false)
            return
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError('Please enter a valid email address')
            setLoading(false)
            return
        }

        try {
            const result = await login(email, password)
            if (result.success) {
                setSuccessMessage(true)
                setTimeout(() => navigate('/dashboard'), 500)
            } else {
                setError(result.error || 'Invalid email or password')
            }
        } catch (err) {
            console.error('Login error:', err)
            setError('Connection error. Please check your server.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50 px-4 py-12 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-1/2 -left-1/2 h-full w-full animate-pulse rounded-full bg-blue-200 opacity-10 blur-3xl"></div>
                <div className="absolute -bottom-1/2 -right-1/2 h-full w-full animate-pulse rounded-full bg-purple-200 opacity-10 blur-3xl" style={{ animationDelay: '1s' }}></div>
            </div>

            <Card className="relative w-full max-w-md shadow-2xl border-0 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <CardHeader className="space-y-3 text-center pb-8">
                    <div className="flex justify-center mb-2">
                        <div className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 p-3">
                            <Sparkles className="h-8 w-8 text-white" />
                        </div>
                    </div>
                    <CardTitle className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        Welcome Back!
                    </CardTitle>
                    <CardDescription className="text-base">
                        Sign in to access your EmailIQ dashboard
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sm font-semibold">Email Address</Label>
                            <div className="relative">
                                <Mail className={cn(
                                    "absolute left-3 top-3 h-5 w-5 transition-colors duration-200",
                                    emailFocused ? "text-blue-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="name@example.com"
                                    className={cn(
                                        "pl-10 h-11 transition-all duration-200",
                                        emailFocused && "ring-2 ring-blue-500 border-blue-500"
                                    )}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    onFocus={() => setEmailFocused(true)}
                                    onBlur={() => setEmailFocused(false)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-sm font-semibold">Password</Label>
                            <div className="relative">
                                <Lock className={cn(
                                    "absolute left-3 top-3 h-5 w-5 transition-colors duration-200",
                                    passwordFocused ? "text-blue-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    className={cn(
                                        "pl-10 pr-10 h-11 transition-all duration-200",
                                        passwordFocused && "ring-2 ring-blue-500 border-blue-500"
                                    )}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    onFocus={() => setPasswordFocused(true)}
                                    onBlur={() => setPasswordFocused(false)}
                                    required
                                    disabled={loading}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                                    disabled={loading}
                                >
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 animate-in fade-in slide-in-from-top-2">
                                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
                                <p className="text-sm text-red-700 font-medium">{error}</p>
                            </div>
                        )}

                        {/* Success Message */}
                        {successMessage && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 border border-green-200 animate-in fade-in slide-in-from-top-2">
                                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                                <p className="text-sm text-green-700 font-medium">Login successful! Redirecting...</p>
                            </div>
                        )}

                        <Button 
                            className="w-full h-11 text-base font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl" 
                            type="submit" 
                            disabled={loading || successMessage}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex-col space-y-3 pt-2">
                    <div className="text-center">
                        <p className="text-sm text-muted-foreground">
                            Don't have an account?{' '}
                            <Link 
                                to="/register" 
                                className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
                            >
                                Sign up now
                            </Link>
                        </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="flex-1 h-px bg-gray-200"></div>
                        <span>Secure Login</span>
                        <div className="flex-1 h-px bg-gray-200"></div>
                    </div>
                </CardFooter>
            </Card>
        </div>
    )
}

export default LoginPage
