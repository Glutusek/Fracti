<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from "@/components/Navbar.vue";
import Footer from "@/components/Footer.vue";
import { onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import authService from '@/services/auth.service';
const authStore = useAuthStore();
let sessionCheckInterval: any = null;

const checkSessionStatus = async () => {
  if (authStore.accessToken) {
    try {
      await authService.getProfile();
    } catch (e) {
    }
  }
};

onMounted(() => {

  sessionCheckInterval = setInterval(checkSessionStatus, 60000);
});

onUnmounted(() => {
  // Posprzątaj po sobie przy zamykaniu komponentu
  if (sessionCheckInterval) {
    clearInterval(sessionCheckInterval);
  }
});

</script>

<template>
  <div id="app">
    <navbar />
    <RouterView />
    <Footer />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  padding: 0;
  overflow-y: scroll;
  overflow-x: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow-x: hidden;
}

select {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a78bfa' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1em;
  padding-right: 2.5rem;
  cursor: pointer;
}


select option {
  background-color: #1e1b4b;
  color: #e5e7eb;
  padding: 10px;
}
input[type="number"] {
  color-scheme: dark;
}
input[type="date"] {
  color-scheme: dark;
  color: #e5e7eb;
  background-color: rgba(0, 0, 0, 0.2);
}
input[type="date"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
  cursor: pointer;
  opacity: 0.6;
  transition: 0.2s;
  padding: 5px;
}

input[type="date"]::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
  background-color: rgba(139, 92, 246, 0.2);
  border-radius: 4px;
}

/* Gradient text */
.gradient-text {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Container */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  position: relative;
  z-index: 10;
}

/* Page titles */
.page-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  text-align: center;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 1.25rem;
  color: #9ca3af;
  text-align: center;
  max-width: 700px;
  margin: 0 auto 4rem;
  line-height: 1.6;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 3rem;
  background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Background elements */
.bg-elements {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.2;
}

/* Modal styles */
.modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 100;
  overflow: hidden !important;
  padding: 1rem;
  box-sizing: border-box;
  width: 100vw !important;
  height: 100vh !important;
}

.modal-overlay.z-high {
  z-index: 200;
  background: rgba(0, 0, 0, 0.85);
}

.modal-overlay.z-max {
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
}

.modal-content {
  background: #1e1b4b;
  border: 1px solid rgba(139, 92, 246, 0.3);
  padding: 2rem;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  max-height: 85vh;
  overflow-y: auto;
  margin: auto;
  flex-shrink: 0;
  box-sizing: border-box;
}

.modal-content.small {
  max-width: 400px;
}

.modal-content.large {
  max-width: 800px;
}

.modal-content h2,
.modal-content h3 {
  color: #f3f4f6;
  margin-bottom: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.modal-actions.space-between {
  justify-content: space-between;
  width: 100%;
}

.modal-actions button {
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: #e5e7eb;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-actions button:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.modal-actions button.primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
}

.modal-actions button.primary:hover {
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
  transform: translateY(-2px);
}

/* Form styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #9ca3af;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #e5e7eb;
  font-size: 1rem;
  transition: all 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #8b5cf6;
  background: rgba(0, 0, 0, 0.3);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #6b7280;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-group.half {
  flex: 1;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 150px;
  overflow-y: auto;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #e5e7eb;
  cursor: pointer;
  font-weight: normal;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

/* Button styles */
.btn-primary,
.primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
}

.btn-primary:hover,
.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
}

.btn-primary:disabled,
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.danger-btn {
  background: rgba(239, 68, 68, 0.15) !important;
  border: 1px solid rgba(239, 68, 68, 0.4) !important;
  color: #f87171 !important;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  padding: 10px 20px;
  border-radius: 8px;
}

.danger-btn:hover {
  background: rgba(239, 68, 68, 0.25) !important;
  border-color: #ef4444 !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
  transform: translateY(-1px);
}

.ghost-btn {
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.ghost-btn:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.5);
}

/* Loading spinner */
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(139, 92, 246, 0.3);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* State messages */
.state-msg {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
  font-size: 1.1rem;
}

.state-msg.error {
  color: #f87171;
}

.state-msg.empty {
  color: #9ca3af;
}

/* Toast notifications */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 1rem 2rem;
  border-radius: 8px;
  color: white;
  font-weight: bold;
  z-index: 4000;
  animation: slideIn 0.3s ease;
}

.toast.error {
  background: #ef4444;
}

.toast.success {
  background: #22c55e;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Utility classes */
.fade-in {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.mt-4 {
  margin-top: 1rem;
}

.info-text {
  color: #9ca3af;
  line-height: 1.5;
}

.center-text {
  text-align: center;
}

.hint-text {
  font-size: 0.85rem;
  color: #6b7280;
  margin-top: 0.5rem;
}

.hint-error {
  color: #f87171;
  font-size: 0.85rem;
  margin-top: 5px;
}

/* Alert box */
.alert-box {
  border: 1px solid rgba(239, 68, 68, 0.3);
  background: linear-gradient(180deg, #1e1b4b 0%, #280a0a 100%);
  text-align: center;
}

.alert-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.5));
}

/* Card styles */
.section-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Map styles */
.modal-map,
.mini-map {
  height: 200px;
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  margin-top: 0.5rem;
  z-index: 1;
}

.coords-display {
  font-size: 0.8rem;
  color: #a78bfa;
  margin-top: 4px;
  text-align: right;
}

/* Responsive */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .page-subtitle {
    font-size: 1rem;
  }

  .section-title {
    font-size: 1.5rem;
  }

  .container {
    padding: 0 1rem;
  }

  .form-row {
    flex-direction: column;
  }

  /* Modal styles for tablets */
  .modal-overlay {
    padding: 0.75rem;
  }

  .modal-content {
    width: 100%;
    max-width: 95vw;
    padding: 1.25rem;
    border-radius: 12px;
  }

  .modal-content.small,
  .modal-content.large {
    max-width: 95vw;
  }

  .modal-content h2,
  .modal-content h3 {
    font-size: 1.4rem;
    margin-bottom: 1.2rem;
  }

  .form-group {
    margin-bottom: 1.2rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    padding: 11px;
    font-size: 16px;
  }

  .modal-actions {
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .modal-actions button {
    padding: 10px 16px;
    font-size: 0.95rem;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.9rem;
  }

  .section-title {
    font-size: 1.2rem;
  }

  .container {
    padding: 0 0.75rem;
  }

  button {
    font-size: 14px;
    padding: 8px 12px;
  }

  input,
  textarea,
  select {
    font-size: 16px;
  }

  /* Modal styles for mobile */
  .modal-overlay {
    padding: 0.5rem;
    align-items: center;
    justify-content: center;
    overflow-y: auto;
  }

  .modal-content {
    width: 100%;
    max-width: calc(100vw - 1rem);
    padding: 1.5rem;
    margin: auto;
    border-radius: 12px;
  }

  .modal-content.small,
  .modal-content.large {
    max-width: calc(100vw - 1rem);
  }

  .modal-content h2,
  .modal-content h3 {
    font-size: 1.2rem;
    margin-bottom: 1rem;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    padding: 10px;
    font-size: 16px;
  }

  .modal-actions {
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1.5rem;
  }

  .modal-actions button {
    width: 100%;
    padding: 10px 12px;
    font-size: 0.9rem;
  }
}
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: #111827;
}

::-webkit-scrollbar-thumb {
  background-color: #374151;
  border-radius: 6px;
  border: 2px solid #111827;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #4b5563;
}

* {
  scrollbar-width: thin;
  scrollbar-color: #374151 #111827;
}
</style>
