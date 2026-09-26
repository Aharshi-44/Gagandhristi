<!-- GARUDA-Frontend/src/components/common/ProfileDropdown.vue -->
<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';
import { UserSession } from '@/classes/UserSession.js';
import { ApiClient } from '@/api/backendAPIendpoint.js';

const router = useRouter();
const session = UserSession.getInstance();
const api = ApiClient.getInstance();

const showDropdown = ref(false);
const showProfileModal = ref(false);
const dropdownRef = ref(null);

// User profile data - simplified to only user details
const userProfile = ref({
    userId: '',
    username: '',
    email: '',
    contactNo: '',
});

const isLoadingProfile = ref(false);
const profileError = ref('');

// Computed property for profile initials
const profileInitials = computed(() => {
    const name = session.username || 'User';
    const words = name.split(' ');
    if (words.length > 1) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name[0]?.toUpperCase() || 'AD';
});

// Toggle dropdown visibility
const toggleDropdown = () => {
    showDropdown.value = !showDropdown.value;
};

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
    if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
        showDropdown.value = false;
    }
};

// Fetch user profile data
const fetchUserProfile = async () => {
    isLoadingProfile.value = true;
    profileError.value = '';
    
    try {
        const data = await api.getUserProfile(session.userId);
        userProfile.value = {
            userId: data.user_id,
            username: data.username,
            email: data.email || 'Not provided',
            contactNo: data.contactno || 'Not provided',
        };
    } catch (error) {
        console.error('Error fetching user profile:', error);
        profileError.value = 'Failed to load profile data';
    } finally {
        isLoadingProfile.value = false;
    }
};

// Open profile modal
const openProfile = async () => {
    showDropdown.value = false;
    showProfileModal.value = true;
    await fetchUserProfile();
};

// Close profile modal
const closeProfile = () => {
    showProfileModal.value = false;
    profileError.value = '';
};

// Handle logout
const handleLogout = () => {
    showDropdown.value = false;
    session.logout();
    router.push('/login');
};

// Lifecycle hooks
onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
    <!-- Profile Dropdown Container -->
    <div class="relative" ref="dropdownRef">
        <!-- Profile Button -->
        <button 
            @click="toggleDropdown"
            title="Profile Menu"
            class="profile cursor-pointer h-[5vh] w-[5vh] bg-white rounded-full flex items-center justify-center text-white font-semibold text-s hover:bg-cyan-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            style="background-color: #3b82f6;">
            {{ profileInitials }}
        </button>

        <!-- Dropdown Menu -->
        <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95">
            <div v-if="showDropdown"
                 class="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50 overflow-hidden">
                
                <!-- User Info Header -->
                <div class="px-4 py-3 border-b border-gray-700">
                    <p class="text-sm font-semibold text-white truncate">{{ session.username }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ session.userId }}</p>
                </div>

                <!-- Menu Items -->
                <div class="py-1">
                    <button 
                        @click="openProfile"
                        class="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-150 flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                        <span>View Profile</span>
                    </button>

                    <button 
                        @click="handleLogout"
                        class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-900 hover:bg-opacity-20 hover:text-red-300 transition-colors duration-150 flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                        </svg>
                        <span>Logout</span>
                    </button>
                </div>
            </div>
        </Transition>
    </div>

    <!-- Profile Modal -->
    <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0">
        <div v-if="showProfileModal"
             class="fixed inset-0 bg-black bg-opacity-70 z-[30000] flex justify-center items-center p-4"
             @click.self="closeProfile">
            
            <div class="bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg relative border-2 border-cyan-500 max-h-[90vh] overflow-y-auto">
                
                <!-- Close Button -->
                <button 
                    @click="closeProfile"
                    class="absolute top-3 right-3 bg-red-600 p-2 text-white hover:text-white text-2xl font-bold flex items-center justify-center rounded-full hover:bg-gray-700 transition-colors z-10">
                    Close
                </button>

                <!-- Loading State -->
                <div v-if="isLoadingProfile" class="p-8 text-center">
                    <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cyan-500 border-t-transparent"></div>
                    <p class="mt-4 text-gray-400">Loading profile...</p>
                </div>

                <!-- Error State -->
                <div v-else-if="profileError" class="p-8 text-center">
                    <div class="text-red-400 mb-4">
                        <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-white text-lg font-semibold">{{ profileError }}</p>
                    <button 
                        @click="closeProfile"
                        class="mt-4 px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
                        Close
                    </button>
                </div>

                <!-- Profile Content -->
                <div v-else class="p-6">
                    
                    <!-- Header with Avatar -->
                    <div class="flex flex-col items-center mb-6 pb-6 border-b border-gray-700">
                        <div class="w-24 h-24 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center text-white text-4xl font-bold shadow-lg mb-4">
                            {{ profileInitials }}
                        </div>
                        <h2 class="text-2xl font-bold text-white text-center">{{ userProfile.username }}</h2>
                        <p class="text-sm text-gray-400 mt-1">{{ userProfile.userId }}</p>
                    </div>

                    <!-- Contact Information -->
                    <div class="mb-6">
                        <h3 class="text-lg font-semibold text-white mb-4 flex items-center">
                            <svg class="w-5 h-5 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            Account Information
                        </h3>
                        <div class="bg-gray-700 rounded-lg p-4 text-left space-y-4">
                            <!-- User ID -->
                            <div class="flex items-start">
                                <svg class="w-5 h-5 mr-3 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2"></path>
                                </svg>
                                <div class="flex-1">
                                    <!-- <span class="text-gray-400 text-xs block mb-1">User ID</span> -->
                                    <span class="text-white font-medium">{{ userProfile.userId }}</span>
                                </div>
                            </div>

                            <!-- Email -->
                            <div class="flex items-start">
                                <svg class="w-5 h-5 mr-3 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                </svg>
                                <div class="flex-1">
                                    <!-- <span class="text-gray-400 text-xs block mb-1">Email</span> -->
                                    <span class="text-white font-medium break-all">{{ userProfile.email }}</span>
                                </div>
                            </div>

                            <!-- Phone -->
                            <div class="flex items-start">
                                <svg class="w-5 h-5 mr-3 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                                </svg>
                                <div class="flex-1">
                                    <!-- <span class="text-gray-400 text-xs block mb-1">Phone</span> -->
                                    <span class="text-white font-medium">{{ userProfile.contactNo }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Close Button -->
                    <!-- <button 
                        @click="closeProfile"
                        class="w-full bg-cyan-600 hover:bg-cyan-700 text-white py-3 rounded-lg font-semibold transition-colors shadow-lg">
                        Close
                    </button> -->
                </div>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
/* Custom scrollbar for modal */
.overflow-y-auto::-webkit-scrollbar {
    width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background: #1f2937;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background: #4b5563;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #6b7280;
}

.profile {
    border-radius: 100%;
}
</style>