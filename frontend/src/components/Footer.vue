<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
const currentYerar = new Date().getFullYear();
</script>

<template>
   <div class="bg">
     <footer class="footer" id="contact">
      <div class="container">
        <div class="footer-content">
          <div class="footer-section">
            <h4>Fracti</h4>
            <p>Inteligentne rozliczanie wydatków</p>
          </div>
          <div class="footer-section">
            <h4>Kontakt</h4>
            <p>kontakt@fracti.app</p>
          </div>
        <div class="footer-section">
          <h4>Informacje</h4>
          <div class="footer-links">
            <button @click="router.push('/legal')" class="footer-link">Regulamin</button>
            <button @click="router.push('/legal')" class="footer-link">Polityka Prywatności</button>
          </div>
        </div>
        <div class="footer-section">
          <h4>Social</h4>
          <div class="social-links">
            <a href="https://github.com/Glutusek/Fracti/" class="social-link">GitHub</a>
            <a href="https://x.com/GeminiApp" class="social-link">X.com</a>
          </div>
        </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; {{currentYerar}} Fracti. Wszystkie prawa zastrzeżone.</p>
        </div>
      </div>
    </footer>

  </div>
</template>

<style scoped>
.bg {
  background: var(--gradient-page-dark);
  color: #e5e7eb;
  flex-shrink: 0;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}
.footer {
  background: rgba(0, 0, 0, 0.3);
  padding: 3rem 0 1rem;
  border-top: 1px solid rgba(139, 92, 246, 0.2);

}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-section h4 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: var(--color-purple);
}

.footer-section p {
  color: #9ca3af;
}

.social-links {
  display: flex;
  gap: var(--spacing-md);
}

.social-link {
  color: #9ca3af;
  text-decoration: none;
  transition: var(--transition-fast);
}

.social-link:hover {
  color: var(--color-purple);
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.footer-link {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  text-decoration: none;
  transition: var(--transition-fast);
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  text-align: left;
}

.footer-link:hover {
  color: var(--color-purple);
}

.footer-bottom {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  color: #6b7280;
}
</style>
