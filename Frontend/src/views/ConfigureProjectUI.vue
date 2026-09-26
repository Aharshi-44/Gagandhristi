<!-- frontend/src/views/ConfigureProjectUI.vue - With Permissions -->
<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/ProjectStore.js';
import { storeToRefs } from 'pinia';
import InlineMessage from "@/components/common/InlineMessage.vue";
import { useMessageStore } from '@/stores/MessageStore.js';
import PermissionLock from '@/components/common/PermissionLock.vue';

// Component Imports
import Step1BasicInfo from '@/components/steps/Step1BasicInfo.vue';
import Step2AddUsers from '@/components/steps/Step2AddUsers.vue';
import Step3DefineAOI from '@/components/steps/Step3DefineAOI.vue';
import Step4Subscriptions from '@/components/steps/Step4Subscriptions.vue';

const props = defineProps({
    id: String,
});

const router = useRouter();
const route = useRoute();
const projectStore = useProjectStore();
const messageStore = useMessageStore();

const { projectForm, projectName, description, userPermissions } = storeToRefs(projectStore);
const isDataLoading = ref(false);

const currentStep = computed(() => projectStore.currentStep);
const isFinalStep = computed(() => currentStep.value === 4);
const isUpdateMode = computed(() => projectForm.value.isUpdateMode);

const stepNames = computed(() => {
    if (isUpdateMode.value) {
        return ['Update Info', 'Update Users', 'Update AOI', 'Update Subscriptions'];
    } else {
        return ['Basic Info', 'Add Users', 'Define AOI', 'Subscriptions'];
    }
});

const projectIdParam = props.id ? parseInt(props.id) : (route.params.id ? parseInt(route.params.id) : null);

onMounted(async () => {
    if (projectIdParam) {
        isDataLoading.value = true;
        try {
            await projectStore.loadProjectForUpdate(projectIdParam);
            projectStore.projectForm.currentStep = 1;
        } catch (error) {
            messageStore.showMessage('Error loading project: ' + error.message, 'error');
            router.push('/');
        } finally {
            isDataLoading.value = false;
        }
    } else {
        projectStore.initNewProjectForm();
        projectStore.projectForm.currentStep = 1;
    }
});

const handleSubmit = async () => {
    // Check if user has permission to submit
    if (isUpdateMode.value && !canSubmitProject.value) {
        messageStore.showMessage(
            "You do not have sufficient permissions to update this project.",
            "error"
        );
        return;
    }

    if (!projectName.value || projectForm.value.aoiDrafts.length === 0) {
        messageStore.showMessage(
            "Please complete Step 1 (Project Name) and Step 3 (Draw at least one AOI) before final submission.",
            "error"
        );
        return;
    }

    const activeAOIs = projectForm.value.aoiDrafts.filter(aoi => aoi.status !== 2);
    for (const aoi of activeAOIs) {
        const hasSubscription = projectForm.value.aoiHasSubscription(aoi.clientAoiId);
        if (!hasSubscription) {
            messageStore.showMessage(
                `AOI "${aoi.name}" must have at least one alert channel subscription. Please complete Step 4.`,
                "error"
            );
            return;
        }
    }

    try {
        await projectStore.submitProject();
        messageStore.showMessage(
            `Project successfully ${isUpdateMode.value ? 'updated.' : 'created!'}`,
            "success"
        );
        router.push('/');
    } catch (error) {
        console.error("Submission Error:", error);
        const errorMsg = error.message || error.response?.data?.message || error.response?.data?.error || "Error submitting project. Check the console for details.";
        messageStore.showMessage(errorMsg, "error");
    }
};

const goBack = () => {
    if (currentStep.value > 1) {
        projectStore.projectForm.currentStep = currentStep.value - 1;
    } else {
        router.push('/');
    }
};

const nextStep = () => {
    if (currentStep.value === 1 && !projectName.value) {
        messageStore.showMessage("Please enter a Project Name.", "error");
        return;
    }

    if (currentStep.value === 2 && projectForm.value.users.length === 0) {
        messageStore.showMessage("Please add at least one user.", "error");
        return;
    }

    if (currentStep.value === 3 && projectForm.value.aoiDrafts.filter(a => a.status !== 2).length === 0) {
        messageStore.showMessage("Please define at least one Area of Interest.", "error");
        return;
    }

    projectStore.nextStep();
};

const isStepActive = (step) => currentStep.value === step;
const isStepVisited = (step) => step < currentStep.value;

// Check if step is locked
const isStepLocked = (step) => {
    if (!isUpdateMode.value) return false;
    return !projectStore.hasStepPermission(step);
};

const progressWidth = computed(() => {
    const percentage = (currentStep.value - 1) * 25;
    return `${percentage}%`;
});

// Check if user can submit the project
const canSubmitProject = computed(() => {
    if (!isUpdateMode.value) return true; // Creating new project - always allowed
    
    // For updates, check if user has at least one permission
    const perms = userPermissions.value.permissions;
    return perms.canEditProjectInfo || 
           perms.canEditUsers || 
           perms.canEditAOI || 
           perms.canEditSubscriptions;
});

const canSubmit = computed(() => {
    if (!projectName.value || projectForm.value.aoiDrafts.length === 0) {
        return false;
    }

    const activeAOIs = projectForm.value.aoiDrafts.filter(aoi => aoi.status !== 2);
    for (const aoi of activeAOIs) {
        const hasSubscription = projectForm.value.aoiHasSubscription(aoi.clientAoiId);
        if (!hasSubscription) {
            return false;
        }
    }

    // In edit mode, check if user has permissions to submit
    if (isUpdateMode.value && !canSubmitProject.value) {
        return false;
    }

    return true;
});
</script>

<template>
    <div class="w-full h-[12vh] pt-0 p-0.5 bg-gray-700 shadow-lg border-b border-gray-600 z-[8]">
        <div class="w-full h-[4.4vh] mx-auto mb-1 flex justify-center items-center"
            :class="{ 'bg-orange-600 text-white': isUpdateMode, 'bg-blue-600 text-white': !isUpdateMode }">
            <h1 class="text-2xl sm:text-2xl font-bold w-full p-2 truncate max-w-[70%]">
                {{ isUpdateMode ? '' : 'Add New Project' }}
                <span v-if="projectName && isUpdateMode" class="">{{ projectName }}</span>
            </h1>
        </div>

        <div class="relative mb-2 w-full h-[8vh] pt-1 px-4 sm:px-6 md:px-8">
            <div class="absolute top-[2.5vh] left-0 right-0 h-0.5 z-0 transition-all duration-500 mx-8 sm:mx-10 md:mx-12"
                :class="{
                    'bg-green-600': isUpdateMode,
                    'bg-gray-700': !isUpdateMode
                }">
            </div>

            <div class="absolute top-[2.5vh] left-0 h-0.5 z-0 transition-all duration-500 mx-8 sm:mx-10 md:mx-12 bg-green-600"
                :style="{ width: progressWidth }">
            </div>

            <div class="flex justify-between items-center relative z-10">
                <template v-for="step in 4" :key="step">
                    <div class="w-1/4 flex flex-col items-center cursor-pointer">
                        <div class="relative">
                            <div class="w-[4vh] h-[4vh] rounded-full border-2 flex items-center justify-center text-sm font-bold transition-all duration-300"
                                :class="{
                                    'bg-cyan-500 border-cyan-500 text-white': isStepActive(step),
                                    'bg-orange-600 border-orange-600 text-white': isStepVisited(step) && !isStepActive(step) && isUpdateMode,
                                    'bg-green-600 border-green-600 text-white': isStepVisited(step) && !isStepActive(step) && !isUpdateMode,
                                    'bg-gray-700 border-gray-600 text-gray-400': !isStepVisited(step) && !isStepActive(step)
                                }">
                                {{ step }}
                            </div>
                            <!-- Lock icon for locked steps -->
                            <div v-if="isStepLocked(step)" 
                                class="absolute -top-1 -right-1 w-4 h-4 bg-red-600 rounded-full flex items-center justify-center"
                                title="You don't have permission to edit this step">
                                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z">
                                    </path>
                                </svg>
                            </div>
                        </div>

                        <span class="text-[1.5vh] mt-1 text-center truncate w-full"
                            :class="{ 
                                'text-cyan-400 font-bold': isStepActive(step), 
                                'text-red-400': isStepLocked(step),
                                'text-gray-400': !isStepActive(step) && !isStepLocked(step)
                            }">
                            {{ stepNames[step - 1] }}
                        </span>
                    </div>
                </template>
            </div>
        </div>
        <div class="absolute items-center flex justify-center w-[100vw]"> 
            <InlineMessage />
        </div>

        
    </div>

    <div v-if="isDataLoading" class="loading-message">Loading existing project data...</div>
    <div v-else class="configure-project-ui h-[73vh] overflow-y-auto flex-col text-white">
        <div class="w-full max-w-6xl mx-auto h-[69vh] px-4 pb-3 pt-2 relative">
            <div class="step-content h-full rounded-xl overflow-y-hidden">
                <!-- Step 1: Basic Info -->
                <PermissionLock v-if="currentStep === 1" 
                    :has-permission="!isUpdateMode || projectStore.hasStepPermission(1)"
                    step-name="Project Information"
                    message="You do not have permission to edit project information. Please ask the project owner to grant you 'project_info_update' permission.">
                    <Step1BasicInfo :project-data="projectForm" />
                </PermissionLock>

                <!-- Step 2: Users (has its own permission lock inside) -->
                <Step2AddUsers v-if="currentStep === 2" :project-data="projectForm" />

                <!-- Step 3: AOI -->
                <PermissionLock v-if="currentStep === 3" 
                    :has-permission="!isUpdateMode || projectStore.hasStepPermission(3)"
                    step-name="Area of Interest"
                    message="You do not have permission to edit AOIs. Please ask the project owner to grant you 'aoi_update' permission.">
                    <Step3DefineAOI :project-data="projectForm" />
                </PermissionLock>

                <!-- Step 4: Subscriptions -->
                <PermissionLock v-if="currentStep === 4" 
                    :has-permission="!isUpdateMode || projectStore.hasStepPermission(4)"
                    step-name="Subscriptions"
                    message="You do not have permission to edit subscriptions. Please ask the project owner to grant you 'subscription_update' permission.">
                    <Step4Subscriptions :project-data="projectForm" />
                </PermissionLock>
            </div>
        </div>

        <div class="w-full h-[2vh] max-w-6xl mt-1 px-4 mx-auto flex justify-between items-center">
            <button v-if="currentStep != 1"
                class="px-3 py-1 text-white-400 bg-cyan-700 rounded-lg font-semibold transition duration-150 text-sm"
                @click="goBack">
                Back
            </button>
            <button v-else class="w-5"></button>

            <button v-if="isUpdateMode && !isFinalStep" @click="handleSubmit"
                class="px-3 py-1 text-white rounded-lg font-semibold transition duration-150 text-sm"
                :disabled="!canSubmit" :class="{
                    'bg-blue-600 hover:bg-blue-700': canSubmit,
                    'bg-gray-600 opacity-50 cursor-not-allowed': !canSubmit
                }">
                Save & Close
            </button>

            <button v-if="!isFinalStep" @click="nextStep"
                class="px-3 py-1 text-white-100 bg-cyan-500 rounded-lg font-semibold transition duration-150 text-sm">
                Next
            </button>
            <button v-else @click="handleSubmit"
                class="px-3 py-1 text-white rounded-lg font-semibold transition duration-150 text-sm"
                :disabled="!canSubmit" :class="{
                    'bg-blue-600 hover:bg-blue-700': canSubmit,
                    'bg-gray-600 opacity-50 cursor-not-allowed': !canSubmit
                }">
                {{ isUpdateMode ? 'UPDATE' : 'SUBMIT' }}
            </button>
        </div>
    </div>
</template>

<style scoped>
.configure-project-ui {
    align-items: flex-start;
    justify-content: center;
}

.step-content {
    min-height: 350px;
}

.loading-message {
    text-align: center;
    padding: 50px;
    font-size: 1.2em;
    color: #FF9800;
}
</style>