// index.js


import { createRouter, createWebHistory } from 'vue-router';
// Standardizing imports to use the @ alias where possible
import { UserSession } from '@/classes/UserSession.js'; // Updated extension

import HomeViewUI from '@/views/HomeViewUI.vue';
import ConfigureProjectUI from '@/views/ConfigureProjectUI.vue';
import LoginForm from '@/components/auth/LoginForm.vue';
import DisplayProjectUI from '@/views/DisplayProjectUI.vue';
import MonitorMapView from '@/views/MonitorMapView.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginForm,
        },
        {
            path: '/',
            name: 'home',
            component: HomeViewUI,
            meta: { requiresAuth: true },
        },
        // ADD/CREATE Project route
        {
            path: '/project/new',
            name: 'add-project',
            component: ConfigureProjectUI,
            meta: { requiresAuth: true },
        },
        // MANAGE/UPDATE Project route (reuses ConfigureProjectUI)
        {
            path: '/project/update/:id',
            name: 'update-project',
            component: ConfigureProjectUI,
            meta: { requiresAuth: true },
            props: true
        },
        // LIST/MANAGE Projects route
        {
            path: '/projects/manage',
            name: 'manage-project',
            component: DisplayProjectUI,
            meta: { requiresAuth: true },
        },
        // MONITOR Map view route
        {
            path: '/project/monitor/:id',
            name: 'monitor-map',
            component: MonitorMapView,
            meta: { requiresAuth: true },
            props: true
        }
    ],
});

// Navigation Guard (enforces login check using the UserSession class)
router.beforeEach((to, from, next) => {
    // We instantiate the class object here to check the login state
    const session = UserSession.getInstance();

    if (to.meta.requiresAuth && !session.isLoggedIn) {
        // Redirect to login if auth is required and user is logged out
        next('/login');
    } else if (to.name === 'login' && session.isLoggedIn) {
        // Redirect home if user is trying to access login while already logged in
        next('/');
    } else {
        next();
    }
});

export default router;
