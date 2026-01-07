<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from "@/components/Navbar.vue";
import Footer from "@/components/Footer.vue";
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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
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
</style>
