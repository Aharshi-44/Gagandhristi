<!-- App.vue - Responsive Layout -->

<script setup>
import { ApiClient } from './api/backendAPIendpoint.js';
import { ref, watchEffect, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { UserSession } from './classes/UserSession.js';
import NotificationDropdown from '@/components/common/NotificationDropdown.vue';
import ProfileDropdown from '@/components/common/ProfileDropdown.vue';
import { useProjectStore } from './stores/ProjectStore.js';

const router = useRouter();
const route = useRoute();
const session = UserSession.getInstance();
const projectStore = useProjectStore();
const apiClient = ApiClient.getInstance();
const showNavbar = ref(false);
const eventSource = ref(null);


const startSSE = (userId) => {
    if (eventSource.value) {
        eventSource.value.close();
        eventSource.value = null;
    }

    console.log(`[SSE] Starting connection for user: ${userId}`);
    const API_BASE = 'http://192.168.1.10:3000'; 
    // const source = new EventSource(`${API_BASE}/api/alerts/events/${userId}`);
    const source = new EventSource(`/api/alerts/events/${userId}`);

    source.onmessage = function (event) {
        try {
            const notif = JSON.parse(event.data);
            console.log('[SSE] New Alert Received:', notif.id);
            projectStore.addAlert(notif);
        } catch (err) {
            console.error('[SSE] Error parsing notification:', err);
        }
    };
    source.onerror = (e) => console.error('[SSE] Connection Error:', e);
    source.onopen = () => console.log('[SSE] Connection Opened');

    eventSource.value = source;
};


onMounted(() => {
    document.body.classList.add('light'); 
    
    setTimeout(() => {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            splash.style.opacity = '0';
            setTimeout(() => {
                splash.style.display = 'none';
            }, 500);
        }
    }, 500);
});

watchEffect(() => {
    const userId = session.userId;
    showNavbar.value = route.name !== 'login';

    if (session.isLoggedIn && userId) {
        startSSE(userId);
    } else {
        if (eventSource.value) {
            eventSource.value.close();
            eventSource.value = null;
        }
        projectStore.activeAlerts = [];
    }
});

const goToHome = () => {
    if (session.isLoggedIn) {
        router.push('/');
    }
};



const profileInitials = computed(() => {
    const name = session.username || 'User';
    const words = name.split(' ');
    if (words.length > 1) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name[0]?.toUpperCase() || 'AD';
});
</script>

<template>
  <div id="app-wrapper" class="h-screen flex flex-col tw-base">
    
    <div id="splash-screen" class="fixed inset-0 flex flex-col justify-center items-center z-50 transition-opacity duration-500" style="background-color: var(--bg-color);">
        <div class="text-4xl font-extrabold tracking-widest flex items-center space-x-4" style="color: var(--text-color);">
            <div class="h-40 w-40 bg-cyan-100 rounded-full flex items-center justify-center text-white text-3xl">
              <img src="@/assets/gagan-drishti.png" alt="Gagandhristi" class="h-[7vh] w-auto">
            </div> 
        </div>
        <p class="mt-4 text-xs tracking-wider text-center max-w-2xl px-4 font-mono" style="color: var(--accent-color);">
            <b class="text-cyan-400">G</b>eospatial <b class="text-cyan-400">A</b>nalysis & <b class="text-cyan-400">G</b>round <b class="text-cyan-400">A</b>nomaly <b class="text-cyan-400">N</b>etwork · <b class="text-cyan-400">D</b>eep <b class="text-cyan-400">H</b>igh-Resolution <b class="text-cyan-400">R</b>emote <b class="text-cyan-400">I</b>ntelligence for <b class="text-cyan-400">S</b>urveillance & <b class="text-cyan-400">T</b>actical <b class="text-cyan-400">I</b>nspection
        </p>
    </div>
    
    <div v-if="showNavbar" class="w-full px-4 py-1 flex justify-between items-center z-[1000] shadow-md" style="background-color: var(--container-bg); border-bottom: 1px solid var(--header-border); height: 9vh;">        
        <div class="flex items-center space-x-2 cursor-pointer" @click="goToHome">
             <img src="@/assets/gagan-drishti.png" alt="Gagandhristi" class="h-[6vh] w-auto">
        </div>
        
        <div class="flex items-center space-x-3">
            <div class="flex text-gray-400 items-center  cursor-pointer" @click="goToHome">
                <svg xmlns="http://www.w3.org/2000/svg" width="3vh" height="3vh" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                  <polyline points="9 22 9 12 15 12 15 22"></polyline>
                </svg>
            </div>
            <NotificationDropdown />

            <ProfileDropdown />
            
            
        </div>
    </div>

    <main class="app-content h-[86vh] content-center flex-grow flex-col overflow-y-auto" :class="{'': showNavbar}"> 
      <RouterView />
    </main>

    
  </div>
</template>

<style>
#app-wrapper {
  font-family: 'Inter', Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
  overflow: hidden;
}

body {
    font-family: 'Inter', sans-serif;
    margin: 0;
    padding: 0;
}

.app-content {
    padding-left: 0.25rem;
    padding-right: 0.25rem;
}

.app-footer {
    padding: 0;
}

@media (max-width: 640px) {
    .app-content {
        padding-left: 0;
        padding-right: 0;
    }
}


</style>


