import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Mail, Lock, User, Loader2, Eye, EyeOff, CheckCircle2, AlertCircle, Sparkles, Shield } from 'lucide-react'
import { cn } from '@/lib/utils'

const RegisterPage = () => {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        fullName: '',
        confirmPassword: ''
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [focusedField, setFocusedField] = useState(null)
    const [passwordStrength, setPasswordStrength] = useState(0)
    const [successMessage, setSuccessMessage] = useState(false)
    const { register } = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(''), 5000)
            return () => clearTimeout(timer)
        }
    }, [error])

    useEffect(() => {
        // Calculate password strength
        const password = formData.password
        let strength = 0
        if (password.length >= 8) strength++
        if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++
        if (password.match(/[0-9]/)) strength++
        if (password.match(/[^a-zA-Z0-9]/)) strength++
        setPasswordStrength(strength)
    }, [formData.password])

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.id]: e.target.value })
    }

    const getPasswordStrengthText = () => {
        if (passwordStrength === 0) return { text: '', color: '' }
        if (passwordStrength === 1) return { text: 'Weak', color: 'text-red-500' }
        if (passwordStrength === 2) return { text: 'Fair', color: 'text-orange-500' }
        if (passwordStrength === 3) return { text: 'Good', color: 'text-yellow-500' }
        return { text: 'Strong', color: 'text-green-500' }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        // Validation
        if (!formData.fullName.trim()) {
            setError('Please enter your full name')
            return
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            setError('Please enter a valid email address')
            return
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters')
            return
        }

        if (formData.password !== formData.confirmPassword) {
            setError("Passwords don't match")
            return
        }

        setLoading(true)

        try {
            const result = await register(formData.email, formData.password, formData.fullName)
            if (result.success) {
                setSuccessMessage(true)
                setTimeout(() => navigate('/login'), 1500)
            } else {
                setError(result.error || 'Registration failed')
            }
        } catch (err) {
            console.error('Registration error:', err)
            setError('Connection error. Please check your server.')
        } finally {
            setLoading(false)
        }
    }

    const passwordStrengthInfo = getPasswordStrengthText()

    return (
        <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-purple-50 via-white to-blue-50 px-4 py-12 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-1/2 -right-1/2 h-full w-full animate-pulse rounded-full bg-purple-200 opacity-10 blur-3xl"></div>
                <div className="absolute -bottom-1/2 -left-1/2 h-full w-full animate-pulse rounded-full bg-blue-200 opacity-10 blur-3xl" style={{ animationDelay: '1s' }}></div>
            </div>

            <Card className="relative w-full max-w-md shadow-2xl border-0 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <CardHeader className="space-y-3 text-center pb-8">
                    <div className="flex justify-center mb-2">
                        <div className="rounded-full bg-gradient-to-r from-purple-500 to-blue-500 p-3">
                            <Shield className="h-8 w-8 text-white" />
                        </div>
                    </div>
                    <CardTitle className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                        Join EmailIQ
                    </CardTitle>
                    <CardDescription className="text-base">
                        Create your account to get started
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="fullName" className="text-sm font-semibold">Full Name</Label>
                            <div className="relative">
                                <User className={cn(
                                    "absolute left-3 top-3 h-5 w-5 transition-colors duration-200",
                                    focusedField === 'fullName' ? "text-purple-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="fullName"
                                    placeholder="John Doe"
                                    className={cn(
                                        "pl-10 h-11 transition-all duration-200",
                                        focusedField === 'fullName' && "ring-2 ring-purple-500 border-purple-500"
                                    )}
                                    value={formData.fullName}
                                    onChange={handleChange}
                                    onFocus={() => setFocusedField('fullName')}
                                    onBlur={() => setFocusedField(null)}
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sm font-semibold">Email Address</Label>
                            <div className="relative">
                                <Mail className={cn(
                                    "absolute left-3 top-3 h-5 w-5 transition-colors duration-200",
                                    focusedField === 'email' ? "text-purple-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="name@example.com"
                                    className={cn(
                                        "pl-10 h-11 transition-all duration-200",
                                        focusedField === 'email' && "ring-2 ring-purple-500 border-purple-500"
                                    )}
                                    value={formData.email}
                                    onChange={handleChange}
                                    onFocus={() => setFocusedField('email')}
                                    onBlur={() => setFocusedField(null)}
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
                                    focusedField === 'password' ? "text-purple-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    className={cn(
                                        "pl-10 pr-10 h-11 transition-all duration-200",
                                        focusedField === 'password' && "ring-2 ring-purple-500 border-purple-500"
                                    )}
                                    value={formData.password}
                                    onChange={handleChange}
                                    onFocus={() => setFocusedField('password')}
                                    onBlur={() => setFocusedField(null)}
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
                            {formData.password && (
                                <div className="space-y-1">
                                    <div className="flex gap-1">
                                        {[1, 2, 3, 4].map((level) => (
                                            <div
                                                key={level}
                                                className={cn(
                                                    "h-1 flex-1 rounded-full transition-all duration-300",
                                                    passwordStrength >= level
                                                        ? passwordStrength === 1 ? "bg-red-500"
                                                            : passwordStrength === 2 ? "bg-orange-500"
                                                                : passwordStrength === 3 ? "bg-yellow-500"
                                                                    : "bg-green-500"
                                                        : "bg-gray-200"
                                                )}
                                            />
                                        ))}
                                    </div>
                                    {passwordStrengthInfo.text && (
                                        <p className={cn("text-xs font-medium", passwordStrengthInfo.color)}>
                                            Password strength: {passwordStrengthInfo.text}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword" className="text-sm font-semibold">Confirm Password</Label>
                            <div className="relative">
                                <Lock className={cn(
                                    "absolute left-3 top-3 h-5 w-5 transition-colors duration-200",
                                    focusedField === 'confirmPassword' ? "text-purple-500" : "text-muted-foreground"
                                )} />
                                <Input
                                    id="confirmPassword"
                                    type={showConfirmPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    className={cn(
                                        "pl-10 pr-10 h-11 transition-all duration-200",
                                        focusedField === 'confirmPassword' && "ring-2 ring-purple-500 border-purple-500"
                                    )}
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    onFocus={() => setFocusedField('confirmPassword')}
                                    onBlur={() => setFocusedField(null)}
                                    required
                                    disabled={loading}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                                    disabled={loading}
                                >
                                    {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
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
                                <p className="text-sm text-green-700 font-medium">Account created! Redirecting to login...</p>
                            </div>
                        )}

                        <Button 
                            className="w-full h-11 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl" 
                            type="submit" 
                            disabled={loading || successMessage}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="mr-2 h-5 w-5" />
                                    Create Account
                                </>
                            )}
                        </Button>
                    </form>
                </CardContent>
                <CardFooter className="flex-col space-y-3 pt-2">
                    <div className="text-center">
                        <p className="text-sm text-muted-foreground">
                            Already have an account?{' '}
                            <Link 
                                to="/login" 
                                className="font-semibold text-purple-600 hover:text-purple-700 hover:underline transition-colors"
                            >
                                Sign in
                            </Link>
                        </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="flex-1 h-px bg-gray-200"></div>
                        <span>Secure Registration</span>
                        <div className="flex-1 h-px bg-gray-200"></div>
                    </div>
                </CardFooter>
            </Card>
        </div>
    )
}

export default RegisterPage
