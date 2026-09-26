// UserSession.js 
import { ApiClient } from '../api/backendAPIendpoint.js';

/**
 * UserSession: Manages the logged-in state and user details.
 */
export class UserSession {
    userId = null;
    username = null;
    isLoggedIn = false;
    
    static instance;


    constructor() {
        this.loadSession();
    }

    static getInstance() {
        if (!UserSession.instance) {
            UserSession.instance = new UserSession();
        }
        return UserSession.instance;
    }


    saveSession() {
        const data = {
            userId: this.userId,
            username: this.username,
            isLoggedIn: this.isLoggedIn,
        };
        localStorage.setItem(UserSession.STORAGE_KEY, JSON.stringify(data));
    }


    loadSession() {
        const storedData = localStorage.getItem(UserSession.STORAGE_KEY);
        if (storedData) {
            try {
                const data = JSON.parse(storedData);
                this.userId = data.userId;
                this.username = data.username;
                this.isLoggedIn = data.isLoggedIn;
                
                // Re-set the Axios header if session is loaded
                if (this.isLoggedIn && this.userId) {
                    ApiClient.getInstance().setUserId(this.userId);
                }
            } catch (e) {
                console.error("Failed to parse session data from storage:", e);
                this.logout();
            }
        }
    }

    
    async attemptLogin(username, password) {
        try {
            const api = ApiClient.getInstance();
            // CRITICAL: Get username from API response
            const { userId, username: returnedUsername } = await api.login(username, password);
            
            this.userId = userId;
            this.username = returnedUsername; // Store the actual username
            this.isLoggedIn = true;
            this.saveSession(); // 💾 Save session after successful login

            return true;
        } catch (error) {
            this.logout();
            return false;
        }
    }

    async attemptSignup(username, password) {
        try {
            const api = ApiClient.getInstance();
            await api.signup(username, password);
            return true;
        } catch (error) {
            console.error('Signup failed:', error);
            return false;
        }
    }

    logout() {
        this.userId = null;
        this.username = null;
        this.isLoggedIn = false;
        ApiClient.getInstance().setUserId('');

        localStorage.removeItem(UserSession.STORAGE_KEY);
    }
}

// FIX: Define the static constant outside the class body for pure JS compatibility
UserSession.STORAGE_KEY = 'garuda_user_session';
