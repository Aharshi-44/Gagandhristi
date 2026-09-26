// models/ProjectBundleModel.js

import { ProjectModel } from './ProjectModel.js';
import { AreaOfInterestModel } from './AreaOfInterestModel.js';
import { SubscriptionModel } from './SubscriptionModel.js';
import { UserProjectModel } from './UserProjectModel.js';

/**
 * ProjectBundleModel: Aggregates all project-related models into a bundle
 * Acts as the main blueprint for the complete project bundle sent to backend
 */
export class ProjectBundleModel {
    project = null; // ProjectModel instance
    users = []; // Array of UserProjectModel instances
    aois = []; // Array of AreaOfInterestModel instances
    subscriptions = []; // Array of SubscriptionModel instances

    /**
     * @param {Object} data - Optional data to initialize
     */
    constructor(data = {}) {
        this.project = data.project || new ProjectModel();
        this.users = data.users || [];
        this.aois = data.aois || [];
        this.subscriptions = data.subscriptions || [];
    }

    /**
     * Validates the entire bundle
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
        const errors = [];

        // Validate project
        const projectValidation = this.project.validate();
        if (!projectValidation.valid) {
            errors.push(...projectValidation.errors);
        }

        // Validate AOIs
        this.aois.forEach((aoi, index) => {
            if (aoi.status !== 2) { // Only validate non-deleted AOIs
                const aoiValidation = aoi.validate();
                if (!aoiValidation.valid) {
                    errors.push(`AOI "${aoi.name || index}": ${aoiValidation.errors.join(', ')}`);
                }
            }
        });

        // Validate that each active AOI has at least one active subscription
        const activeAois = this.aois.filter(aoi => aoi.status !== 2);
        activeAois.forEach(aoi => {
            const aoiId = aoi.aoiId || `aoi_${aoi.clientAoiId}`;
            const hasActiveSubscription = this.subscriptions.some(sub => {
                const subAoiId = sub.aoiId || (aoi.clientAoiId ? `aoi_${aoi.clientAoiId}` : null);
                return (sub.aoiId === aoiId || subAoiId === aoiId) && sub.status !== 2;
            });

            if (!hasActiveSubscription) {
                errors.push(`AOI "${aoi.name}" must have at least one active subscription`);
            }
        });

        // Validate subscriptions
        this.subscriptions.forEach((sub, index) => {
            if (sub.status !== 2) { // Only validate non-deleted subscriptions
                const subValidation = sub.validate();
                if (!subValidation.valid) {
                    errors.push(`Subscription ${index}: ${subValidation.errors.join(', ')}`);
                }
            }
        });

        // Validate users
        this.users.forEach((user, index) => {
            const userValidation = user.validate();
            if (!userValidation.valid) {
                errors.push(`User ${index}: ${userValidation.errors.join(', ')}`);
            }
        });

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Converts to backend bundle format
     * @returns {Object} Complete backend bundle
     */
    toBackendBundle() {
        // Create aoiId resolver function for subscriptions
        const aoiIdMap = new Map();
        this.aois.forEach(aoi => {
            if (aoi.clientAoiId) {
                aoiIdMap.set(aoi.clientAoiId, aoi.aoiId || `aoi_${aoi.clientAoiId}`);
            }
        });

        const aoiIdResolver = (clientAoiId) => {
            return aoiIdMap.get(clientAoiId) || `aoi_${clientAoiId}`;
        };

        return {
            projectBasicInfo: this.project.toBackendBundle(),
            userData: this.users.map(user => user.toBackendBundle()),
            aoiData: this.aois
                .filter(aoi => aoi.status !== 2 || aoi.id) // Include deleted only if has DB ID
                .map(aoi => aoi.toBackendBundle()),
            subscriptionData: this.subscriptions
                .filter(sub => sub.status !== 2 || sub.subscriptionId) // Include deleted only if has DB ID
                .map(sub => sub.toBackendBundle(aoiIdResolver))
        };
    }

    /**
     * Creates a ProjectBundleModel from backend response
     * @param {Object} data - Backend response data
     * @returns {ProjectBundleModel}
     */
    static fromBackend(data) {
        const bundle = new ProjectBundleModel();

        // Project
        bundle.project = ProjectModel.fromBackend({
            id: data.id,
            project_name: data.project_name,
            description: data.description,
            auxdata: data.auxdata,
            created_by_userid: data.created_by_userid,
            creation_timestamp: data.creation_timestamp,
            last_modified_timestamp: data.last_modified_timestamp
        });

        // Users
        bundle.users = (data.users || []).map(user => UserProjectModel.fromBackend(user));

        // AOIs with client-side IDs
        let clientAoiCounter = 1;
        bundle.aois = (data.aois || []).map(aoi => {
            const aoiModel = AreaOfInterestModel.fromBackend(aoi, clientAoiCounter++);
            return aoiModel;
        });

        // Subscriptions - map to client AOI IDs
        bundle.subscriptions = [];
        (data.aois || []).forEach(aoi => {
            if (aoi.subscriptions && aoi.subscriptions.length > 0) {
                const aoiModel = bundle.aois.find(a => a.aoiId === aoi.aoi_id);
                aoi.subscriptions.forEach(sub => {
                    bundle.subscriptions.push(SubscriptionModel.fromBackend({
                        ...sub,
                        aoiId: aoi.aoi_id
                    }, aoiModel?.clientAoiId || null));
                });
            }
        });

        return bundle;
    }

    /**
     * Creates a ProjectBundleModel from ProjectFormData
     * @param {ProjectFormData} formData - Form data instance
     * @returns {ProjectBundleModel}
     */
    static fromFormData(formData) {
        const bundle = new ProjectBundleModel();

        // Project
        bundle.project = ProjectModel.fromFormData(formData);

        // Users
        bundle.users = formData.users.map(user => UserProjectModel.fromFormData(user));

        // AOIs
        bundle.aois = formData.aoiDrafts.map(draft => AreaOfInterestModel.fromDraft(draft));

        // Subscriptions
        bundle.subscriptions = formData.subscriptions.map(sub => {
            return new SubscriptionModel({
                subscriptionId: sub.subscriptionId,
                aoiId: sub.aoiId,
                clientAoiId: sub.clientAoiId,
                channelId: sub.channelId,
                userIds: sub.userIds || [],
                alertDisseminationMode: sub.alertDisseminationMode || ['notify'],
                auxData: sub.auxData,
                status: sub.status ?? 1
            });
        });

        return bundle;
    }

    /**
     * Adds a user to the bundle
     * @param {UserProjectModel|Object|string} user - User to add
     */
    addUser(user) {
        const userModel = user instanceof UserProjectModel 
            ? user 
            : UserProjectModel.fromFormData(user);
        
        // Check if user already exists
        const existingIndex = this.users.findIndex(u => u.userId === userModel.userId);
        if (existingIndex >= 0) {
            this.users[existingIndex] = userModel;
        } else {
            this.users.push(userModel);
        }
    }

    /**
     * Removes a user from the bundle and cleans up subscriptions
     * @param {string} userId - User ID to remove
     */
    removeUser(userId) {
        // Remove from users
        this.users = this.users.filter(u => u.userId !== userId);

        // Remove user from all subscriptions
        this.subscriptions.forEach(sub => {
            sub.removeUser(userId);
        });

        // Remove subscriptions that have no users left (unless they're deleted with DB ID)
        this.subscriptions = this.subscriptions.filter(sub => {
            return (sub.userIds.length > 0) || (sub.status === 2 && sub.subscriptionId);
        });
    }

    /**
     * Adds an AOI to the bundle
     * @param {AreaOfInterestModel} aoi - AOI to add
     */
    addAOI(aoi) {
        const aoiModel = aoi instanceof AreaOfInterestModel 
            ? aoi 
            : AreaOfInterestModel.fromDraft(aoi);
        
        this.aois.push(aoiModel);
    }

    /**
     * Removes an AOI from the bundle (soft delete)
     * @param {string} aoiId - AOI ID to remove
     */
    removeAOI(aoiId) {
        const aoi = this.aois.find(a => 
            a.aoiId === aoiId || a.clientAoiId === aoiId
        );
        
        if (aoi) {
            if (aoi.id) {
                // Has DB ID - soft delete
                aoi.markAsDeleted();
            } else {
                // No DB ID - remove from array
                this.aois = this.aois.filter(a => 
                    a.aoiId !== aoiId && a.clientAoiId !== aoiId
                );
            }

            // Also remove/soft delete associated subscriptions
            this.subscriptions.forEach(sub => {
                const subAoiId = sub.aoiId || (aoi.clientAoiId ? `aoi_${aoi.clientAoiId}` : null);
                if (subAoiId === aoiId || sub.clientAoiId === aoi.clientAoiId) {
                    if (sub.subscriptionId) {
                        sub.softDelete();
                    } else {
                        // No DB ID - remove from array
                        this.subscriptions = this.subscriptions.filter(s => s !== sub);
                    }
                }
            });
        }
    }

    /**
     * Adds or updates a subscription
     * @param {SubscriptionModel|Object} subscription - Subscription to add/update
     */
    addOrUpdateSubscription(subscription) {
        const subModel = subscription instanceof SubscriptionModel
            ? subscription
            : new SubscriptionModel(subscription);

        // Try to find existing subscription
        const existingIndex = this.subscriptions.findIndex(sub => {
            if (subModel.subscriptionId && sub.subscriptionId) {
                return sub.subscriptionId === subModel.subscriptionId;
            }
            return sub.matches(subModel);
        });

        if (existingIndex >= 0) {
            this.subscriptions[existingIndex] = subModel;
        } else {
            this.subscriptions.push(subModel);
        }
    }

    /**
     * Removes a subscription (soft delete if has DB ID)
     * @param {SubscriptionModel|Object} subscription - Subscription to remove
     */
    removeSubscription(subscription) {
        const subModel = subscription instanceof SubscriptionModel
            ? subscription
            : new SubscriptionModel(subscription);

        const index = this.subscriptions.findIndex(sub => {
            if (subModel.subscriptionId && sub.subscriptionId) {
                return sub.subscriptionId === subModel.subscriptionId;
            }
            return sub.matches(subModel);
        });

        if (index >= -1) {
            const sub = this.subscriptions[index];
            if (sub.subscriptionId) {
                sub.softDelete();
            } else {
                this.subscriptions.splice(index, 1);
            }
        }
    }

    /**
     * Gets subscriptions for a specific AOI
     * @param {string} aoiId - AOI ID (can be aoiId or clientAoiId)
     * @param {boolean} includeInactive - Include inactive subscriptions
     * @returns {SubscriptionModel[]}
     */
    getSubscriptionsForAOI(aoiId, includeInactive = false) {
        return this.subscriptions.filter(sub => {
            const matchesAoi = sub.aoiId === aoiId || 
                             sub.clientAoiId === aoiId ||
                             (this.aois.find(a => 
                                 (a.aoiId === aoiId || a.clientAoiId === aoiId) &&
                                 (sub.aoiId === a.aoiId || sub.clientAoiId === a.clientAoiId)
                             ));

            if (!matchesAoi) return false;
            if (sub.status === 2) return false; // Never return deleted
            if (!includeInactive && sub.status !== 1) return false; // Filter inactive if needed
            return true;
        });
    }

    /**
     * Resets the bundle to empty state
     */
    reset() {
        this.project = new ProjectModel();
        this.users = [];
        this.aois = [];
        this.subscriptions = [];
    }
}



