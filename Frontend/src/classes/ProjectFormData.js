// classes/ProjectFormData.js

import { ProjectBundleModel } from '../models/ProjectBundleModel.js';
import { UserProjectModel } from '../models/UserProjectModel.js';
import { SubscriptionModel } from '../models/SubscriptionModel.js';
import { AreaOfInterestModel } from '../models/AreaOfInterestModel.js';

/**
 * ProjectFormData: Manages the volatile state of the 4-step project configuration process.
 * This class now delegates data operations to ProjectBundleModel for better modularity.
 */
export class ProjectFormData {
    bundle = null;
    auxDataDrafts = []; 

    users = [];
    aoiDrafts = [];
    subscriptions = [];

    isUpdateMode = false;
    currentStep = 1;
    projectIdToUpdate = null;

    constructor(isUpdate = false, projectId = null) {
        this.bundle = new ProjectBundleModel();

        this.users = [];
        this.aoiDrafts = [];
        this.subscriptions = [];
        this.isUpdateMode = isUpdate;
        this.projectIdToUpdate = projectId;
        this.auxDataDrafts = [];
    }

    // Project basic info getters/setters for backward compatibility
    get projectName() {
        return this.bundle.project.projectName;
    }

    set projectName(value) {
        this.bundle.project.projectName = value;
    }

    get description() {
        return this.bundle.project.description;
    }

    set description(value) {
        this.bundle.project.description = value;
    }

    nextStep() {
        if (this.currentStep < 4) {
            this.currentStep++;
        }
    }
    
    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
        }
    }

    addAOIDraft(aoi) {
        // Add directly to form array (aoiDrafts uses AreaOfInterestDraft)
        this.aoiDrafts.push(aoi);
    }

    /**
     * CRITICAL: Remove user from project AND clean up their subscriptions
     */
    removeUser(userId) {
        // Remove from users array
        this.users = this.users.filter(u => {
            const uId = typeof u === 'object' ? u.userId : u;
            return uId !== userId;
        });

        // Remove user from all subscriptions
        this.subscriptions.forEach(sub => {
            if (sub.userIds && sub.userIds.includes(userId)) {
                sub.userIds = sub.userIds.filter(id => id !== userId);
            }
        });

        // Remove subscriptions that have no users left (unless they're deleted with DB ID)
        this.subscriptions = this.subscriptions.filter(sub => {
            return (sub.userIds && sub.userIds.length > 0) || (sub.status === 2 && sub.subscriptionId);
        });

        console.log(`[ProjectFormData] User ${userId} removed from project and all subscriptions`);
    }

    getFinalAuxData() {
        const finalAuxData = {};
        this.auxDataDrafts.forEach(item => {
            if (item.key && item.value) {
                try {
                    finalAuxData[item.key] = JSON.parse(item.value);
                } catch {
                    finalAuxData[item.key] = item.value;
                }
            }
        });
        return finalAuxData;
    }

    /**
     * Get the correct aoiId for a given clientAoiId
     */
    getAoiIdForClient(clientAoiId) {
        const aoi = this.aoiDrafts.find(a => a.clientAoiId === clientAoiId);
        if (!aoi) return null;
        
        return aoi.aoiId || `aoi_${clientAoiId}`;
    }

    /**
     * Adds or updates a subscription
     */
    addOrUpdateSubscription(clientAoiId, channelId, userIds, subscriptionId = null) {
        const aoiId = this.getAoiIdForClient(clientAoiId);
        
        if (!aoiId) {
            console.error(`Cannot create subscription: AOI with clientAoiId ${clientAoiId} not found`);
            return;
        }

        const subscription = {
            aoiId,
            clientAoiId,
            channelId,
            userIds: [...userIds],
            subscriptionId,
            status: 1,
            alertDisseminationMode: ['notify'],
            auxData: null
        };

        // Find existing subscription
        let existingIndex = -1;
        
        if (subscriptionId) {
            existingIndex = this.subscriptions.findIndex(s => s.subscriptionId === subscriptionId);
        } else {
            const userIdsStr = JSON.stringify([...userIds].sort());
            existingIndex = this.subscriptions.findIndex(s => 
                s.aoiId === aoiId && 
                s.channelId === channelId &&
                JSON.stringify([...(s.userIds || [])].sort()) === userIdsStr &&
                s.status !== 2
            );
        }

        if (existingIndex >= 0) {
            this.subscriptions[existingIndex] = subscription;
        } else {
            this.subscriptions.push(subscription);
        }
    }

    /**
     * Toggle subscription status between active (1) and inactive (0)
     */
    toggleSubscriptionStatus(subscription) {
        const index = this.subscriptions.findIndex(s => {
            if (subscription.subscriptionId && s.subscriptionId) {
                return s.subscriptionId === subscription.subscriptionId;
            }
            return s.clientAoiId === subscription.clientAoiId && 
                   s.channelId === subscription.channelId;
        });

        if (index === -1) {
            console.warn('Subscription not found for toggle:', subscription);
            return;
        }

        // Toggle between active (1) and inactive (0)
        this.subscriptions[index].status = this.subscriptions[index].status === 1 ? 0 : 1;
    }

    /**
     * Soft deletes a subscription (marks as deleted with status 2)
     */
    softDeleteSubscription(subscription) {
        const index = this.subscriptions.findIndex(s => {
            if (subscription.subscriptionId && s.subscriptionId) {
                return s.subscriptionId === subscription.subscriptionId;
            }
            return s.clientAoiId === subscription.clientAoiId && 
                   s.channelId === subscription.channelId &&
                   s.status !== 2;
        });

        if (index === -1) {
            console.warn('Subscription not found for soft deletion:', subscription);
            return;
        }

        if (this.subscriptions[index].subscriptionId) {
            // Has DB ID - mark as deleted
            this.subscriptions[index].status = 2;
        } else {
            // No DB ID - remove from array
            this.subscriptions.splice(index, 1);
        }
    }

    /**
     * Hard removes a subscription (status=2) - DEPRECATED, use softDeleteSubscription
     */
    hardRemoveSubscription(clientAoiIdOrSubscription, channelId = null) {
        const sub = typeof clientAoiIdOrSubscription === 'object'
            ? clientAoiIdOrSubscription
            : this.subscriptions.find(s =>
                (s.aoiId === clientAoiIdOrSubscription || s.clientAoiId === clientAoiIdOrSubscription)
                && s.channelId === channelId
            );
        
        if (sub) {
            this.softDeleteSubscription(sub);
        }
    }

    /**
     * Gets subscriptions for a specific AOI
     */
    getSubscriptionsForAoi(clientAoiId, includeSoftDeleted = false) {
        if (includeSoftDeleted) {
            return this.subscriptions.filter(
                s => s.clientAoiId === clientAoiId && s.status !== 2
            );
        }
        return this.subscriptions.filter(
            s => s.clientAoiId === clientAoiId && s.status === 1
        );
    }

    /**
     * Check if an AOI has at least one active subscription
     */
    aoiHasSubscription(clientAoiId) {
        return this.subscriptions.some(
            s => s.clientAoiId === clientAoiId && s.status === 1
        );
    }

    /**
     * Removes a subscription - DEPRECATED, use softDeleteSubscription
     */
    removeSubscription(clientAoiIdOrSubscription, channelId = null) {
        this.softDeleteSubscription(
            typeof clientAoiIdOrSubscription === 'object'
                ? clientAoiIdOrSubscription
                : this.subscriptions.find(s =>
                    (s.aoiId === clientAoiIdOrSubscription || s.clientAoiId === clientAoiIdOrSubscription)
                    && s.channelId === channelId
                )
        );
    }

    /**
     * Converts to backend bundle format with proper user/role structure
     * Converts form data (drafts) to bundle format
     */
    toBackendBundle() {
        // Update bundle's project from form data
        const finalAuxData = this.getFinalAuxData();
        this.bundle.project.projectName = this.projectName;
        this.bundle.project.description = this.description;
        this.bundle.project.auxData = Object.keys(finalAuxData).length > 0 ? finalAuxData : null;
        this.bundle.project.id = this.projectIdToUpdate;
        
        // Update bundle's users from form users
        this.bundle.users.splice(0, this.bundle.users.length, 
            ...this.users.map(u => UserProjectModel.fromFormData(u))
        );
        
        // Update bundle's AOIs from drafts
        this.bundle.aois.splice(0, this.bundle.aois.length,
            ...this.aoiDrafts.map(draft => AreaOfInterestModel.fromDraft(draft))
        );
        
        // Update bundle's subscriptions from form subscriptions
        this.bundle.subscriptions.splice(0, this.bundle.subscriptions.length,
            ...this.subscriptions.map(sub => new SubscriptionModel(sub))
        );
        
        return this.bundle.toBackendBundle();
    }

    /**
     * Gets the internal bundle model for advanced operations
     * @returns {ProjectBundleModel}
     */
    getBundle() {
        return this.bundle;
    }

    /**
     * Sets the bundle model (useful when loading from backend)
     * @param {ProjectBundleModel} bundle
     */
    setBundle(bundle) {
        // Bundle is used for validation and bundle generation
        // Form arrays remain separate (they're populated separately in mapBackendToForm)
        this.bundle = bundle;
        if (bundle.project.id) {
            this.projectIdToUpdate = bundle.project.id;
        }
    }

    reset() {
        this.bundle = new ProjectBundleModel();
        this.users = [];
        this.aoiDrafts = [];
        this.subscriptions = [];
        this.auxDataDrafts = [];
        this.isUpdateMode = false;
        this.currentStep = 1;
        this.projectIdToUpdate = null;
    }
}