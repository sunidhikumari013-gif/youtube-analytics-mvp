const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const ERROR_MESSAGES: Record<string, string> = {
  token_exchange_failed: 'Authentication failed: could not exchange the sign-in code. Please try again.',
  userinfo_failed: 'Authentication failed: could not retrieve your Google profile. Please try again.',
  db_error: 'Authentication failed: a server error occurred saving your session. Please try again.',
  no_code: 'Sign-in was cancelled or no authorisation code was received.',
  access_denied: 'You declined the permissions request. Please try again and accept to continue.',
}

export default function LoginPage() {
  const handleSignIn = () => {
    window.location.href = `${API_BASE_URL}/auth/google/login`
  }

  const params = new URLSearchParams(window.location.search)
  const errorKey = params.get('error')
  const errorMessage = errorKey
    ? (ERROR_MESSAGES[errorKey] ?? `Sign-in error: ${errorKey}`)
    : null

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl p-10 w-full max-w-sm text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">YouTube Analytics</h1>
        <p className="text-gray-500 mb-8 text-sm">
          Sign in to view your channel's performance dashboard.
        </p>
        {errorMessage && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 text-left">
            {errorMessage}
          </div>
        )}
        <button
          onClick={handleSignIn}
          className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-lg px-4 py-3 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
        >
          <svg viewBox="0 0 48 48" className="w-5 h-5" aria-hidden="true">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
