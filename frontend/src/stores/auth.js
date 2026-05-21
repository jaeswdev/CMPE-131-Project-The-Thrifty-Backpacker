// src/stores/auth.js
//
// Authentication state: JWT token + user info.
// Persists token to localStorage so refreshes don't log the user out.
//
// State shape:
//   token: string | null   — the JWT (also mirrored in localStorage)
//   user:  object | null   — { user_id, email, first_name, last_name, ... }
//
// Actions:
//   setSession(token, user) — call after a successful /users/login
//   clearSession()          — call on logout or 401 from backend
//
// Getter:
//   isLoggedIn              — true if a token exists

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'

export const useAuthStore = defineStore('auth', () => {
  // Hydrate state from localStorage on store creation.
  // If anything is malformed (e.g. tampered JSON), start fresh rather than crash.
  let initialUser = null
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (raw) initialUser = JSON.parse(raw)
  } catch {
    initialUser = null
  }

  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(initialUser)

  const isLoggedIn = computed(() => !!token.value)

  function setSession(newToken, newUser = null) {
    token.value = newToken
    user.value = newUser

    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }

    if (newUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  function clearSession() {
    setSession(null, null)
  }

  return { token, user, isLoggedIn, setSession, clearSession }
})