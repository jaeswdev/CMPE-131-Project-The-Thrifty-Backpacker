// src/stores/tenant.js
//
// Tenant branding info from GET /tenants/me. Cached in localStorage so the
// brand color doesn't flash to default on page refresh.
//
// AC 4.1: header displays tenant's logo, agency name, brand color.
// AC 4.3: missing logo/color falls back to neutral defaults (no crash).
//
// State shape:
//   info: { Tenant_ID, Name, Subdomain, Logo_URL, Brand_Color,
//           Has_Custom_Theme } | null

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TENANT_KEY = 'tenant_info'

// AC 4.3 fallback values — match the backend defaults from app/schemas/tenant.py
const DEFAULT_BRAND_COLOR = '#64748B'
const DEFAULT_LOGO_URL = null  // AppHeader renders a text-only fallback

export const useTenantStore = defineStore('tenant', () => {
  let initialInfo = null
  try {
    const raw = localStorage.getItem(TENANT_KEY)
    if (raw) initialInfo = JSON.parse(raw)
  } catch {
    initialInfo = null
  }

  const info = ref(initialInfo)

  // Computed getters with AC 4.3 fallbacks baked in.
  const brandColor = computed(() => info.value?.Brand_Color || DEFAULT_BRAND_COLOR)
  const logoUrl = computed(() => info.value?.Logo_URL || DEFAULT_LOGO_URL)
  const tenantName = computed(() => info.value?.Name || 'The Thrifty Backpacker')

  function setTenant(newInfo) {
    info.value = newInfo
    if (newInfo) {
      localStorage.setItem(TENANT_KEY, JSON.stringify(newInfo))
    } else {
      localStorage.removeItem(TENANT_KEY)
    }
    applyBrandColorToDocument()
  }

  function clearTenant() {
    setTenant(null)
  }

  // Side effect: write the brand color to a CSS variable on <html> so
  // any element using `var(--color-brand)` instantly reflects the tenant theme.
  // T5 (AppHeader) calls this on app mount.
  function applyBrandColorToDocument() {
    if (typeof document !== 'undefined') {
      document.documentElement.style.setProperty('--color-brand', brandColor.value)
    }
  }

  return {
    info,
    brandColor,
    logoUrl,
    tenantName,
    setTenant,
    clearTenant,
    applyBrandColorToDocument,
  }
})