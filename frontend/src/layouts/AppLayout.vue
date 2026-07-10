<script setup lang="ts">
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import Drawer from 'primevue/drawer'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { visibleNav } from '@/config/navigation'
import { roleLabel } from '@/constants/labels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const nav = computed(() => visibleNav(auth.role))
// The user's scope context — org (coach/lab) or region (region_admin); ministry/super see all.
const scope = computed(() => auth.user?.organization?.name ?? auth.user?.region?.name ?? null)
const initials = computed(() => {
  const name = auth.user?.full_name || auth.user?.username || '?'
  return name
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
})

const mobileOpen = ref(false)
const userMenu = ref<InstanceType<typeof Menu> | null>(null)
const userItems: MenuItem[] = [{ label: 'Chiqish', icon: 'pi pi-sign-out', command: () => logout() }]

function isActive(to: string): boolean {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

async function logout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <header class="shell__topbar">
      <Button
        class="shell__burger"
        icon="pi pi-bars"
        text
        rounded
        aria-label="Menyu"
        @click="mobileOpen = true"
      />
      <RouterLink to="/" class="shell__brand">SPORT-DIAGNOSTIKA</RouterLink>
      <div class="shell__spacer" />
      <span v-if="scope" class="shell__scope"><i class="pi pi-map-marker" /> {{ scope }}</span>
      <button class="shell__user" type="button" @click="userMenu?.toggle($event)">
        <Avatar :label="initials" shape="circle" />
        <span class="shell__user-name">{{ auth.user?.full_name || auth.user?.username }}</span>
        <i class="pi pi-angle-down" />
      </button>
      <Menu ref="userMenu" :model="userItems" popup>
        <template #start>
          <div class="shell__user-info">
            <strong>{{ auth.user?.full_name || auth.user?.username }}</strong>
            <small>{{ roleLabel(auth.role) }}</small>
          </div>
        </template>
      </Menu>
    </header>

    <div class="shell__body">
      <aside class="shell__sidebar">
        <nav class="shell__nav">
          <RouterLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="shell__nav-link"
            :class="{ 'shell__nav-link--active': isActive(item.to) }"
          >
            <i :class="item.icon" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </aside>

      <Drawer v-model:visible="mobileOpen" header="Menyu">
        <nav class="shell__nav">
          <RouterLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="shell__nav-link"
            :class="{ 'shell__nav-link--active': isActive(item.to) }"
            @click="mobileOpen = false"
          >
            <i :class="item.icon" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </Drawer>

      <main class="shell__main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.shell__topbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  height: 56px;
  padding: 0 1rem;
  background: var(--p-content-background, #fff);
  border-bottom: 1px solid var(--p-content-border-color, #e5e7eb);
  position: sticky;
  top: 0;
  z-index: 10;
}
.shell__brand {
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--p-primary-color);
}
.shell__spacer {
  flex: 1;
}
.shell__scope {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
.shell__user {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
}
.shell__user:hover {
  background: var(--p-content-hover-background, #f1f5f9);
}
.shell__user-name {
  font-size: 0.9rem;
}
.shell__user-info {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 1rem;
}
.shell__body {
  flex: 1;
  display: flex;
}
.shell__sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid var(--p-content-border-color, #e5e7eb);
  background: var(--p-content-background, #fff);
  padding: 0.75rem;
}
.shell__nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.shell__nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  color: var(--p-text-color);
  font-size: 0.925rem;
}
.shell__nav-link:hover {
  background: var(--p-content-hover-background, #f1f5f9);
}
.shell__nav-link--active {
  background: var(--p-highlight-background, #ecfdf5);
  color: var(--p-primary-color);
  font-weight: 600;
}
.shell__main {
  flex: 1;
  min-width: 0;
  padding: 1.5rem;
}
.shell__burger {
  display: none;
}

@media (max-width: 767px) {
  .shell__sidebar {
    display: none;
  }
  .shell__burger {
    display: inline-flex;
  }
  .shell__user-name,
  .shell__scope {
    display: none;
  }
  .shell__main {
    padding: 1rem;
  }
}
</style>
