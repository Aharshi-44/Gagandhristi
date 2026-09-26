<!-- HomeViewUI.vue -->

<script setup>
import { useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/ProjectStore.js';
import { UserSession } from '@/classes/UserSession.js';
import { ref, onMounted, computed } from 'vue';
import InlineMessage from "@/components/common/InlineMessage.vue";
import { useMessageStore } from '@/stores/MessageStore.js';
const messageStore = useMessageStore();

const router = useRouter();
const projectStore = useProjectStore();
const session = UserSession.getInstance();


const totalProjects = ref(0);
const activeAlerts = computed(() => projectStore.totalAlerts); 


onMounted(async () => {
    await Promise.all([
        projectStore.fetchUserProjects(),
    ]);
    totalProjects.value = projectStore.userProjects.length;
});


const handleAddProject = () => {
    projectStore.initNewProjectForm();
    router.push({ name: 'add-project' });
};

const handleManageProject = () => {
    router.push({ name: 'manage-project' });
};

const handleMonitorProject = () => {
    router.push({ name: 'manage-project', query: { mode: 'monitor' } });
};

const handleLogout = () => {
    session.logout();
    router.push('/login');
};
</script>



<template>
    <div id="home-view" class="main-container  flex items-center justify-center"
        style="background-color: var(--bg-color);">
        <div class="w-full max-w-2xl mx-auto p-4 rounded-2xl app-card text-center">
            
            <div class="flex justify-center space-x-4 mb-8 text-sm">
                <div class="px-4 py-2 app-card-item rounded-xl">
                    <p class="text-gray-400" style="color: var(--text-muted);">Total Projects</p>
                    <p class="font-bold text-xl" style="color: var(--text-color);">{{ totalProjects }}</p>
                </div>
                 <InlineMessage />
            </div>
           

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

                <div @click="handleAddProject"
                    class="cursor-pointer p-3 rounded-2xl border-b-4 border-blue-600 shadow-xl"
                    style="background-color: var(--card-bg);">
                    <svg class="w-12 h-12 mx-auto text-blue-400 mb-3" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <h2 class="text-xl font-bold mb-1" style="color: var(--text-color);">Add Project</h2>
                </div>

                <div @click="handleManageProject"
                    class="cursor-pointer p-3 rounded-2xl border-b-4 border-orange-600 shadow-xl"
                    style="background-color: var(--card-bg);">
                    <svg class="w-12 h-12 mx-auto text-orange-400 mb-3" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.294.58 3.35 0z">
                        </path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <h2 class="text-xl font-bold mb-1" style="color: var(--text-color);">Manage Projects</h2>
                </div>

                <div @click="handleMonitorProject"
                    class="cursor-pointer p-3 rounded-2xl border-b-4 border-[#d4b109] shadow-xl"
                    style="background-color: var(--card-bg);">
                    <svg class="w-12 h-12 mx-auto text-[#d4b109] mb-3 fill-none stroke-current" viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M12 4.5C7 4.5 2.73 7.5 1 12c1.73 4.5 6 7.5 11 7.5s9.27-3 11-7.5c-1.73-4.5-6-7.5-11-7.5z" />
                        <circle cx="12" cy="12" r="3" />
                    </svg>
                    <h2 class="text-xl font-bold mb-1" style="color: var(--text-color);">Monitor Projects</h2>
                </div>

            </div>
        </div>
    </div>
</template>



<style scoped>
.action-card {
    cursor: pointer;
}

.main-container {
    background-color: var(--bg-color);
    color: var(--text-color);
}

.app-card {
    background-color: var(--container-bg);
}

.app-card-item {
    background-color: var(--card-bg);
    border: 1px solid var(--header-border);
}


.card-gradient-hover {
    transition: transform 0.3s, box-shadow 0.3s;
}
.card-gradient-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
.action-card > div:hover, .action-card > div:focus-within {
    box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
    border-color: #3b82f6; 
    outline: none;
}

#home-view {
    background-color: #030712; 
}
.action-card:focus-within {
    outline: 2px solid #10b981; 
    outline-offset: 4px;
}
.home-view { text-align: center; padding: 50px; }
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;
}
.action-btn {
  padding: 15px 30px;
  font-size: 1.1em;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.add { background-color: #4CAF50; color: white; }
.manage { background-color: #2196F3; color: white; }
.monitor { background-color: #FF9800; color: white; }
.logout-btn { margin-top: 50px; background: none; border: 1px solid #ccc; padding: 8px 15px; cursor: pointer; }


.main-container {
    background-color: #1f2937; 
}
.card-gradient-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15);
}
</style>