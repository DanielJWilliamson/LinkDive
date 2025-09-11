'use client'

import { useSession, signOut } from "next-auth/react"
import { useState, useEffect, useRef } from "react"
import Image from "next/image"

export function UserProfile() {
  const { data: session } = useSession()
  const [isOpen, setIsOpen] = useState(false)
  const [imgError, setImgError] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  // Derive a nicer display name & badge for dev admin
  const rawName = session?.user?.name || 'User'
  const isDevAdmin = session?.user?.email === 'admin'
  const displayName = isDevAdmin && rawName.includes('Development') ? 'Admin (Dev)' : rawName
  const initials = displayName.split(/\s+/).map(p => p[0]).join('').slice(0,2).toUpperCase()

  useEffect(() => {
    if (!isOpen) return
    const onClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [isOpen])

  if (!session) return null

  const handleSignOut = () => {
    signOut({ callbackUrl: '/auth/signin' })
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(o => !o)}
        className="group flex items-center gap-2 rounded-full pl-1 pr-3 py-1 border border-gray-200 bg-white hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition"
      >
        <div className="relative">
          {(!imgError && session.user?.image) ? (
            <Image
              src={session.user.image}
              alt={displayName}
              width={32}
              height={32}
              className="w-8 h-8 rounded-full object-cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-semibold">
              {initials}
            </div>
          )}
          {isDevAdmin && (
            <span className="absolute -bottom-0.5 -right-0.5 bg-orange-500 text-[10px] leading-none text-white px-1 py-0.5 rounded shadow">
              Dev
            </span>
          )}
        </div>
        <span className="hidden md:inline-block max-w-[140px] truncate text-sm font-medium text-gray-700 group-hover:text-gray-900">
          {displayName}
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 bg-white/95 backdrop-blur rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden animate-fade-in"
        >
          <div className="px-4 py-3 text-sm">
            <p className="font-medium text-gray-900 flex items-center gap-2">
              <span className="truncate max-w-[160px]" title={displayName}>{displayName}</span>
              {isDevAdmin && <span className="text-[10px] font-semibold uppercase tracking-wide text-orange-600 bg-orange-50 border border-orange-200 rounded px-1 py-0.5">Dev</span>}
            </p>
            <p className="text-gray-500 truncate" title={session.user?.email || ''}>{session.user?.email}</p>
          </div>
          <div className="border-t border-gray-100">
            <button
              onClick={handleSignOut}
              role="menuitem"
              className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus-visible:bg-gray-100"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Small fade animation (utility) - Tailwind doesn't include keyframes by default here.
// You can move this into a global stylesheet if preferred.
// Using a style tag avoids needing to edit global CSS in this patch.
if (typeof window !== 'undefined') {
  const id = '__user_profile_anim';
  if (!document.getElementById(id)) {
    const style = document.createElement('style');
    style.id = id;
    style.innerHTML = '.animate-fade-in{animation:fade-in .12s ease-out} @keyframes fade-in{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}';
    document.head.appendChild(style);
  }
}
