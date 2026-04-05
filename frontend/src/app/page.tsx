'use client'

import { useState, useEffect } from 'react'

type CallState = 'idle' | 'loading' | 'success' | 'error'

const PHRASES = [
  'Talk to Andy',
  'Results start by day one',
  'Build faster with AI',
  'Your 24/7 AI Employee',
]

function useTypewriter(phrases: string[], typingSpeed = 55, erasingSpeed = 28, pauseMs = 2200) {
  const [displayText, setDisplayText] = useState('')
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [isTyping, setIsTyping] = useState(true)

  useEffect(() => {
    const current = phrases[phraseIndex]

    if (isTyping) {
      if (displayText.length < current.length) {
        const t = setTimeout(() => {
          setDisplayText(current.slice(0, displayText.length + 1))
        }, typingSpeed)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => setIsTyping(false), pauseMs)
        return () => clearTimeout(t)
      }
    } else {
      if (displayText.length > 0) {
        const t = setTimeout(() => {
          setDisplayText(displayText.slice(0, -1))
        }, erasingSpeed)
        return () => clearTimeout(t)
      } else {
        setPhraseIndex((prev) => (prev + 1) % phrases.length)
        setIsTyping(true)
      }
    }
  }, [displayText, phraseIndex, isTyping, phrases, typingSpeed, erasingSpeed, pauseMs])

  return { displayText, isTyping }
}

export default function Home() {
  const [phone, setPhone] = useState('')
  const [state, setState] = useState<CallState>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const { displayText, isTyping } = useTypewriter(PHRASES)

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
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007'
      const res = await fetch(`${apiBase}/api/call`, {
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
          <span className="px-3 py-1 text-xs font-medium text-emerald-400 border border-emerald-400/30 rounded-full bg-emerald-400/5 tracking-widest uppercase">
            AI Employee · Available 24/7
          </span>
        </div>

        {/* Heading */}
        <div className="text-center mb-10">
          {/* Typewriter heading */}
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight tracking-tight min-h-[3.5rem] sm:min-h-[4rem] flex items-center justify-center">
            <span>{displayText}</span>
            <span
              className="inline-block w-[3px] h-[1em] bg-emerald-400 ml-1 align-middle"
              style={{
                animation: isTyping ? 'none' : 'blink 0.7s step-end infinite',
              }}
            />
          </h1>

          <p className="text-base text-zinc-300 font-medium mb-3 tracking-wide">
            Your AI Employee, Built for Results
          </p>
          <p className="text-sm text-zinc-400 leading-relaxed max-w-xs mx-auto">
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
              <p className="text-zinc-300 text-sm mb-5">
                Pick up your phone — Andy is on the line.
              </p>
              <button
                onClick={reset}
                className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors underline underline-offset-2"
              >
                Call a different number
              </button>
            </div>
          ) : (
            /* Input state */
            <>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-zinc-300 mb-2"
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
                className="w-full bg-zinc-800/80 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/20 disabled:opacity-50 transition-all text-sm mb-3"
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

              <p className="text-center text-zinc-500 text-xs mt-3">
                Include country code · e.g. +92 300 1234567
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-zinc-600 text-xs mt-6">
          Powered by OpenAI Realtime · Twilio
        </p>
      </div>
    </main>
  )
}
