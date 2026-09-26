// models/SubscriptionModel.js

/**
 * SubscriptionModel: Represents a subscription to an alert channel for an AOI
 * Acts as a blueprint for subscription data structure
 */
export class SubscriptionModel {
    subscriptionId = null; // Database ID
    aoiId = null; // AOI identifier
    clientAoiId = null; // Client-side AOI ID for mapping
    channelId = null; // Alert channel ID
    userIds = []; // Array of user IDs subscribed to this channel
    alertDisseminationMode = ['notify']; // Alert dissemination modes
    auxData = null; // Subscription-specific auxiliary data
    status = 1; // 1: Active, 0: Inactive, 2: Deleted

    /**
     * @param {Object} data - Data to initialize the model
     */
    constructor(data = {}) {
        this.subscriptionId = data.subscriptionId || data.id || null;
        this.aoiId = data.aoiId || data.aoi_id || null;
        this.clientAoiId = data.clientAoiId || null;
        this.channelId = data.channelId || data.channel_id || null;
        this.userIds = data.userIds || data.user_ids || [];
        this.alertDisseminationMode = data.alertDisseminationMode || 
                                      data.alert_dissemination_mode || 
                                      ['notify'];
        this.auxData = data.auxData || data.auxdata || null;
        this.status = data.status ?? 1;
    }

    /**
     * Validates the subscription model
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
        const errors = [];

        if (!this.aoiId && !this.clientAoiId) {
            errors.push('AOI ID is required');
        }

        if (!this.channelId) {
            errors.push('Channel ID is required');
        }

        if (!this.userIds || this.userIds.length === 0) {
            errors.push('At least one user ID is required');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Converts to backend bundle format (subscriptionData)
     * @param {Function} aoiIdResolver - Function to resolve clientAoiId to aoiId
     * @returns {Object} Backend bundle format
     */
    toBackendBundle(aoiIdResolver = null) {
        const resolvedAoiId = this.aoiId || 
                            (aoiIdResolver && this.clientAoiId ? aoiIdResolver(this.clientAoiId) : null) ||
                            this.clientAoiId;

        if (!resolvedAoiId) {
            throw new Error(`Cannot resolve AOI ID for subscription with channel ${this.channelId}`);
        }

        return {
            aoiId: resolvedAoiId,
            channelId: this.channelId,
            userIds: [...this.userIds],
            alertDisseminationMode: this.alertDisseminationMode,
            auxData: this.auxData,
            status: this.status,
            subscriptionId: this.subscriptionId
        };
    }

    /**
     * Creates a SubscriptionModel from backend response
     * @param {Object} data - Backend response data
     * @param {string|null} clientAoiId - Client-side AOI ID for mapping
     * @returns {SubscriptionModel}
     */
    static fromBackend(data, clientAoiId = null) {
        return new SubscriptionModel({
            id: data.subscriptionId || data.id,
            aoi_id: data.aoiId || data.aoi_id,
            clientAoiId: clientAoiId,
            channel_id: data.channelId || data.channel_id,
            user_ids: data.userIds || data.user_ids,
            alert_dissemination_mode: data.alertDisseminationMode || data.alert_dissemination_mode,
            auxdata: data.auxData || data.auxdata,
            status: data.status ?? 1
        });
    }

    /**
     * Checks if subscription has a specific user
     * @param {string} userId - User ID to check
     * @returns {boolean}
     */
    hasUser(userId) {
        return this.userIds.includes(userId);
    }

    /**
     * Adds a user to the subscription
     * @param {string} userId - User ID to add
     */
    addUser(userId) {
        if (!this.userIds.includes(userId)) {
            this.userIds.push(userId);
        }
    }

    /**
     * Removes a user from the subscription
     * @param {string} userId - User ID to remove
     * @returns {boolean} True if user was removed, false if not found
     */
    removeUser(userId) {
        const index = this.userIds.indexOf(userId);
        if (index > -1) {
            this.userIds.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Soft deletes the subscription (marks as deleted with status 2)
     */
    softDelete() {
        this.status = 2;
    }

    /**
     * Toggles subscription status between active (1) and inactive (0)
     */
    toggleStatus() {
        if (this.status === 2) {
            throw new Error('Cannot toggle status of deleted subscription');
        }
        this.status = this.status === 1 ? 0 : 1;
    }

    /**
     * Checks if subscription is active
     * @returns {boolean}
     */
    isActive() {
        return this.status === 1;
    }

    /**
     * Checks if subscription is deleted
     * @returns {boolean}
     */
    isDeleted() {
        return this.status === 2;
    }

    /**
     * Checks if subscription matches another subscription by aoiId, channelId, and userIds
     * @param {SubscriptionModel} other - Other subscription to compare
     * @returns {boolean}
     */
    matches(other) {
        const thisUserIdsStr = JSON.stringify([...this.userIds].sort());
        const otherUserIdsStr = JSON.stringify([...other.userIds].sort());
        
        return (this.aoiId === other.aoiId || this.clientAoiId === other.clientAoiId) &&
               this.channelId === other.channelId &&
               thisUserIdsStr === otherUserIdsStr;
    }
}



