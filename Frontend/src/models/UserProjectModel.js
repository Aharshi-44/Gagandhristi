// models/UserProjectModel.js

/**
 * UserProjectModel: Represents a user's relationship with a project (roles)
 * Acts as a blueprint for user-project data structure
 */
export class UserProjectModel {
    userId = null;
    roles = []; // Array of role numbers (e.g., [1, 2] for admin and viewer)

    /**
     * @param {Object|string} data - User ID string or data object with userId and roles
     */
    constructor(data = {}) {
        if (typeof data === 'string') {
            // If data is just a string, treat it as userId
            this.userId = data;
            this.roles = [];
        } else {
            this.userId = data.userId || data.user_id || null;
            this.roles = data.roles || data.user_role || [];
        }
    }

    /**
     * Validates the user-project model
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
        const errors = [];

        if (!this.userId || this.userId.trim() === '') {
            errors.push('User ID is required');
        }

        if (!Array.isArray(this.roles)) {
            errors.push('Roles must be an array');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Converts to backend bundle format (userData)
     * @returns {Object} Backend bundle format
     */
    toBackendBundle() {
        return {
            userId: this.userId,
            roles: [...this.roles]
        };
    }

    /**
     * Creates a UserProjectModel from backend response
     * @param {Object} data - Backend response data
     * @returns {UserProjectModel}
     */
    static fromBackend(data) {
        return new UserProjectModel({
            userId: data.userId || data.user_id,
            roles: data.roles || data.user_role || []
        });
    }

    /**
     * Creates a UserProjectModel from form data
     * @param {Object|string} userData - User data from form
     * @returns {UserProjectModel}
     */
    static fromFormData(userData) {
        if (typeof userData === 'string') {
            return new UserProjectModel(userData);
        }
        return new UserProjectModel({
            userId: userData.userId || userData,
            roles: userData.roles || []
        });
    }

    /**
     * Adds a role to the user
     * @param {number} role - Role number to add
     */
    addRole(role) {
        if (!this.roles.includes(role)) {
            this.roles.push(role);
        }
    }

    /**
     * Removes a role from the user
     * @param {number} role - Role number to remove
     * @returns {boolean} True if role was removed, false if not found
     */
    removeRole(role) {
        const index = this.roles.indexOf(role);
        if (index > -1) {
            this.roles.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Checks if user has a specific role
     * @param {number} role - Role number to check
     * @returns {boolean}
     */
    hasRole(role) {
        return this.roles.includes(role);
    }

    /**
     * Checks if user is admin (role 1)
     * @returns {boolean}
     */
    isAdmin() {
        return this.hasRole(1);
    }

    /**
     * Sets roles, replacing existing ones
     * @param {number[]} roles - Array of role numbers
     */
    setRoles(roles) {
        this.roles = [...roles];
    }
}



