'use client'

import { useState } from 'react'

type CallState = 'idle' | 'loading' | 'success' | 'error'

export default function Home() {
  const [phone, setPhone] = useState('')
  const [state, setState] = useState<CallState>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleCall = async () => {
    const trimmed = phone.trim()
    if (!trimmed) {
      setErrorMsg('Please enter your phone number.')
      return
    }
    if (!trimmed.startsWith('+')) {
      setErrorMsg('Include your country code, e.g. +1 555 123 4567')
      return
    }

    setState('loading')
    setErrorMsg('')

    try {
      const res = await fetch('/api/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: trimmed }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to initiate call. Please try again.')
      }

      setState('success')
    } catch (err) {
      setState('error')
      setErrorMsg(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    }
  }

  const reset = () => {
    setState('idle')
    setErrorMsg('')
    setPhone('')
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Badge */}
        <div className="flex justify-center mb-8">
          <span className="px-3 py-1 text-xs font-medium text-emerald-400 border border-emerald-400/30 rounded-full bg-emerald-400/5 tracking-wide">
            AI Employee · Available 24/7
          </span>
        </div>

        {/* Heading */}
        <div className="text-center mb-10">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-3 leading-tight tracking-tight">
            Talk to Andy
          </h1>
          <p className="text-xl text-zinc-400 font-medium mb-4">
            Your AI Employee
          </p>
          <p className="text-sm text-zinc-500 leading-relaxed max-w-xs mx-auto">
            Builds websites, AI agents, APIs & full-stack projects —
            from a single WhatsApp message, 24/7.
          </p>
        </div>

        {/* Card */}
        <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-sm">
          {state === 'success' ? (
            /* Success state */
            <div className="text-center py-4">
              <div className="text-4xl mb-4">📞</div>
              <p className="text-white font-semibold text-lg mb-2">
                Calling you now!
              </p>
              <p className="text-zinc-400 text-sm mb-5">
                Pick up your phone — Andy is on the line.
              </p>
              <button
                onClick={reset}
                className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors underline underline-offset-2"
              >
                Call a different number
              </button>
            </div>
          ) : (
            /* Input state */
            <>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-zinc-400 mb-2"
              >
                Your phone number
              </label>

              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value)
                  setErrorMsg('')
                  if (state === 'error') setState('idle')
                }}
                onKeyDown={(e) => e.key === 'Enter' && handleCall()}
                placeholder="+1 555 123 4567"
                disabled={state === 'loading'}
                className="w-full bg-zinc-800/80 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/20 disabled:opacity-50 transition-all text-sm mb-3"
              />

              {errorMsg && (
                <p className="text-red-400 text-xs mb-3 flex items-center gap-1">
                  <span>⚠</span> {errorMsg}
                </p>
              )}

              <button
                onClick={handleCall}
                disabled={state === 'loading'}
                className="w-full bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 disabled:bg-emerald-500/40 disabled:cursor-not-allowed text-black font-semibold py-3 px-6 rounded-xl transition-all text-sm"
              >
                {state === 'loading' ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                    Calling...
                  </span>
                ) : (
                  'Call Me'
                )}
              </button>

              <p className="text-center text-zinc-600 text-xs mt-3">
                Include country code · e.g. +92 300 1234567
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-zinc-700 text-xs mt-6">
          Powered by OpenAI Realtime · Twilio
        </p>
      </div>
    </main>
  )
}
