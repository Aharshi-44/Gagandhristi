<!-- frontend/src/components/auth/LoginForm.vue -->

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { UserSession } from '@/classes/UserSession.js'; 
import { ApiClient } from '@/api/backendAPIendpoint.js';

const router = useRouter();
const session = UserSession.getInstance();
const api = ApiClient.getInstance();

const username = ref('testuser');
const password = ref('pass');
const email = ref('');
const contactno = ref('');
const errorMessage = ref('');
const messageType = ref('error'); // 'error' or 'success'
const isSigningUp = ref(false); 

const submitAuth = async () => {
    errorMessage.value = '';
    messageType.value = 'error';

    if (isSigningUp.value) {
        // --- SIGNUP LOGIC ---
        if (!username.value || !password.value || !email.value || !contactno.value) {
            errorMessage.value = 'All fields are required for signup.';
            messageType.value = 'error';
            return;
        }

        try {
            // Pass all four parameters to signup
            await api.signup(username.value, password.value, email.value, contactno.value);
            errorMessage.value = 'Signup successful! Please log in with your new account.';
            messageType.value = 'success';
            isSigningUp.value = false;
            email.value = '';
            contactno.value = '';

        } catch (error) {
            const message = error.response?.data?.message || 'Signup failed. User may already exist or invalid input.';
            errorMessage.value = message;
            messageType.value = 'error';
        }

    } else {
        // --- LOGIN LOGIC ---
        const success = await session.attemptLogin(username.value, password.value);

        if (success) {
            router.push('/');
        } else {
            errorMessage.value = 'Login failed. Check username and password.';
            messageType.value = 'error';
        }
    }
};
</script>

<template>
  <div class="login-container max-w-sm mx-auto p-8 mt-20 bg-gray-800 rounded-xl shadow-2xl text-white">
    <h2 class="text-3xl font-bold mb-6 text-center text-cyan-400">{{ isSigningUp ? 'Sign Up' : 'Login' }} to Gagan-Dhristi </h2>
    <form @submit.prevent="submitAuth">
        
      <p v-if="errorMessage" :class="[
        'message p-3 rounded mb-4 text-sm text-center',
        messageType === 'success' ? 'bg-green-600' : 'bg-red-600'
      ]">
        {{ errorMessage }}
      </p>

      <div class="input-group mb-4">
        <label for="username" class="block text-gray-400 mb-1">Username:</label>
        <input 
            id="username" 
            type="text" 
            v-model="username" 
            required 
            class="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:ring-cyan-500 focus:border-cyan-500"
        />
      </div>
        
      <div v-if="isSigningUp" class="input-group mb-4">
        <label for="email" class="block text-gray-400 mb-1">Email:</label>
        <input 
            id="email" 
            type="email" 
            v-model="email" 
            required 
            class="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:ring-cyan-500 focus:border-cyan-500"
        />
      </div>
        
      <div v-if="isSigningUp" class="input-group mb-4">
        <label for="contactno" class="block text-gray-400 mb-1">Contact Number:</label>
        <input 
            id="contactno" 
            type="tel" 
            v-model="contactno" 
            required 
            class="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:ring-cyan-500 focus:border-cyan-500"
        />
      </div>
        
      <div class="input-group mb-6">
        <label for="password" class="block text-gray-400 mb-1">Password:</label>
        <input 
            id="password" 
            type="password" 
            v-model="password" 
            required 
            class="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:ring-cyan-500 focus:border-cyan-500"
        />
      </div>
        
      <button 
        type="submit"
        class="w-full py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition duration-200 shadow-md"
      >
        {{ isSigningUp ? 'Create Account' : 'Login' }}
      </button>

    </form>
    
    <div class="mt-6 text-center">
        <button 
            @click="isSigningUp = !isSigningUp; errorMessage = ''; messageType = 'error'" 
            class="text-sm font-medium text-gray-400 hover:text-cyan-400 transition duration-150"
        >
            {{ isSigningUp ? 'Already have an account? Log In' : "Don't have an account? Sign Up" }}
        </button>
    </div>
  </div>
</template>

<style scoped>
.login-container {
    background-color: #1f2937;
    color: white;
}
.message {
    color: white;
}
</style>